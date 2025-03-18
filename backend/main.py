import json
import os
import re
import sys

import pdfplumber

from backend.agents.classify_moderator_intent import ClassifyModeratorIntent
from backend.agents.extract_management import ExtractManagement
from backend.log_config import logger

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
ERROR_CURSOR_FILE = "failed_files.json"

def save_extracted_text(
    transcript: dict, document_name: str, output_base_path: str = "raw_transcript"
):
    """Save the extracted text to a file."""
    output_dir_path = os.path.join(output_base_path, document_name)
    os.makedirs(output_base_path, exist_ok=True)
    with open(f"{output_dir_path}.txt", "w") as file:
        for _, text in transcript.items():
            file.write(text)
            file.write("\n\n")
    logger.info("Saved transcript text to file\n")


def get_document_transcript(filepath: str):
    """Creates a text transcript of the given pdf document."""
    transcript = {}
    try:
        with pdfplumber.open(filepath) as pdf:
            logger.debug("Loaded document")
            page_number = 1
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # remove newlines, present throughout transcript
                    cleaned_text = re.sub(r"\n", " ", text)
                    transcript[page_number] = cleaned_text
                    page_number += 1
        return transcript
    except Exception:
        logger.exception("Could not load file %s", filepath)


def test_documents(test_dir_path: str, test_all:bool=False):
    """Test all documents in a directory for concall parsing."""
    if os.path.exists(ERROR_CURSOR_FILE):
        with open(ERROR_CURSOR_FILE) as file:
            error_files = set(json.load(file))

    if not test_all:
        files_to_test = error_files
    else:
        files_to_test = set(os.listdir(test_dir_path))
    
    for path in files_to_test:
        try:
            filepath = os.path.join(test_dir_path, path)
            logger.info("Testing %s \n", path)

            transcript = get_document_transcript(filepath)
            save_extracted_text(transcript, path, "raw_transcript")

            dialogues = parse_conference_call(transcript_dict=transcript)
            save_output(dialogues, "output", os.path.basename(path))
        
        except Exception:
            error_files.add(path)
            logger.exception("Error while processing file %s", )
    
    with open(ERROR_CURSOR_FILE, 'w') as file:
        json.dump(list(error_files), file)


class ConferenceCallParser:
    """Class to parse conference call transcript."""

    def __init__(self):
        self.speaker_pattern = re.compile(
            r"(?P<speaker>[A-Za-z\s]+):\s*(?P<dialogue>(?:.*(?:\n(?![A-Za-z\s]+:).*)*)*)",
            re.MULTILINE,
        )
        self.current_analyst = None
        self.last_speaker = None

    def clean_text(self, text: str) -> str:
        """Remove extra spaces, normalize case, and ensure consistency."""
        return re.sub(r"\s+", " ", text).strip().lower()

    def extract_company_name(self, text: str) -> str:
        """Extract company name that appears after 'Yours faithfully'.

        This handles the case where an email is present on the first page of
        the pdf, so the input text should be of the first page.
        """
        pattern = r"Yours faithfully,\s*For\s*(.*?)\s*_"
        match = re.search(pattern, text)
        return match.group(1) if match else "Company name not found"

    def extract_management_team(self, text) -> list[dict[str, str]]:
        """Extract management team members and their designations.

        Handles case where names of all management personnel participating in
        call are present on one page.
        """
        # ! possible issue with type hints in ExtractManagement, need to verify
        try:
            response = ExtractManagement.process(page_text=text)
            response = json.loads(response)
            return response
        except Exception:
            logger.exception("Could not extract management from text")
            return None

    def extract_dialogues(self, transcript_dict: dict[int, str]) -> dict:
        """Extract dialogues and classify stages."""
        dialogues = {
            "commentary_and_future_outlook": [],
            "analyst_discussion": {},
            "end": [],
        }

        # iterate over pages
        for _, text in transcript_dict.items():
            # Add leftover text before speaker pattern to last speaker
            # If not first page of concall
            if self.last_speaker:
                if self.last_speaker == "Moderator":
                    logger.debug(
                        "Skipping moderator statement as it is not needed anymore."
                    )
                else:
                    # analyst or management, get their name
                    first_speaker_match = self.speaker_pattern.search(text)
                    if first_speaker_match:
                        leftover_text = text[: first_speaker_match.start()].strip()
                        if leftover_text:
                            # Append leftover text (speech) to the last speaker's dialogue
                            logger.debug(
                                f"Appending leftover text to {self.last_speaker}"
                            )
                            # TODO: refer to actual data to create model, example
                            if self.current_analyst:
                                dialogues["analyst_discussion"][self.current_analyst][
                                    "dialogue"
                                ][-1]["dialogue"] += (" " + leftover_text)
                            else:
                                dialogues["commentary_and_future_outlook"][-1][
                                    "dialogue"
                                ] += (" " + leftover_text)

            # Extract all speakers in that page
            matches = self.speaker_pattern.finditer(text)

            # TODO: why don't we replace self.speaker_pattern.finditer with matches?
            # ? does speaker pattern find speakers in the text or something else?
            if not any(self.speaker_pattern.finditer(text)) and text.strip():
                # If no matches and text exists, append to the last speaker's dialogue
                # this happens when previous speaker (last speaker on previous page) is
                # the only one talking here, it is continuation of speech started on previous page
                logger.debug(
                    f"No speaker pattern found, appending text to {self.last_speaker}"
                )
                if self.current_analyst:
                    dialogues["analyst_discussion"][self.current_analyst]["dialogue"][
                        -1
                    ]["dialogue"] += " " + self.clean_text(text)
                else:
                    dialogues["commentary_and_future_outlook"][-1][
                        "dialogue"
                    ] += " " + self.clean_text(text)

            # need explanation of regex here
            for match in matches:
                speaker = match.group("speaker").strip()
                dialogue = match.group("dialogue")
                logger.debug(f"Speaker found: {speaker}")
                self.last_speaker = speaker  # Update last speaker

                if speaker == "Moderator":
                    logger.debug(
                        "Moderator statement found, giving it for classification"
                    )
                    response = ClassifyModeratorIntent.process(dialogue=dialogue)
                    response = json.loads(response)
                    logger.info(f"Response from Moderator classifier: {response}")
                    intent = response["intent"]
                    if intent == "new_analyst_start":
                        analyst_name = response["analyst_name"]
                        analyst_company = response["analyst_company"]
                        self.current_analyst = analyst_name
                        logger.debug(f"Current analyst set to: {self.current_analyst}")
                        dialogues["analyst_discussion"][self.current_analyst] = {
                            "analyst_company": analyst_company,
                            "dialogue": [],
                        }
                    logger.debug(
                        "Skipping moderator statement as it is not needed anymore."
                    )
                    continue

                # ? why would intent have a reference before assignment error,
                # what is the text in this case
                if intent == "opening":
                    dialogues["commentary_and_future_outlook"].append(
                        {
                            "speaker": speaker,
                            "dialogue": self.clean_text(dialogue),
                        }
                    )
                elif intent == "new_analyst_start":
                    logger.debug(f"Analyst name: {self.current_analyst}")
                    dialogues["analyst_discussion"][self.current_analyst][
                        "dialogue"
                    ].append(
                        {
                            "speaker": speaker,
                            "dialogue": self.clean_text(dialogue),
                        }
                    )
                elif intent == "end":
                    dialogues["end"].append(
                        {
                            "speaker": speaker,
                            "dialogue": self.clean_text(dialogue),
                        }
                    )

        return dialogues


def extract_management_team_from_text(text: str, management_team: dict) -> dict:
    """Extract management dialogues from text until the next speaker."""
    extracted_dialogues = {}  # To store extracted dialogues

    # Create regex pattern to find each management member and what they spoke
    # extracts all management name and speech pairs in a given text
    # ? but what if some other guy talks in between? is this handled beforehand?
    management_pattern = (
        r"("
        + "|".join(re.escape(name) for name in management_team.keys())
        + r")(.*?)(?=(?:"
        + "|".join(re.escape(name) for name in management_team.keys())
        + r")|$)"
    )
    # ? what does finditer, group and dotall do
    matches = re.finditer(management_pattern, text, re.DOTALL)

    # ? what is the input and output here - how are dialogues extracted? i need logs to understand
    for match in matches:
        speaker = match.group(1)
        dialogue = match.group(2).strip()
        extracted_dialogues[speaker] = dialogue

    return extracted_dialogues


def parse_conference_call(transcript_dict: dict[int, str]) -> dict:
    """Main function to parse and print conference call information."""
    parser = ConferenceCallParser()
    management_team = {}
    extracted_text = ""
    # Extract company name and management team
    # TODO: need to add an extra if in page 2,
    # else case should handle case like reliance (no names given)
    for page_number, text in transcript_dict.items():
        if page_number == 1:
            extracted_text += text
            # generalize for pages 1 and 2?
            if "MANAGEMENT" in text:
                # If first page contains management info, remove from doc, parse it
                logger.debug(f"Page number popped:{page_number}")
                transcript_dict.pop(page_number)
                break
        if page_number == 2:
            # add check for management here, if not present, assume reliance case
            logger.debug(f"Page number popped:{page_number}")
            extracted_text += text
            transcript_dict.pop(1)
            transcript_dict.pop(page_number)
            break

    management_team = parser.extract_management_team(text=extracted_text)

    logger.debug(management_team)

    # Check if moderator exists
    # Can't this be put inside that if? are we using this later?
    moderator_found = any("Moderator:" in text for text in transcript_dict.values())

    if moderator_found:
        # Extract dialogues
        dialogues = parser.extract_dialogues(transcript_dict)
    else:
        # ?why do we do things differently if the moderator is not present?
        logger.debug("No moderator found, extracting management team from text")
        dialogues = extract_management_team_from_text(
            " ".join(transcript_dict.values()), management_team
        )

    logger.info(json.dumps(dialogues, indent=4))
    return dialogues


def save_output(dialogues, output_base_path, document_name):
    """Save dialogues to JSON files in the specified output path."""
    for dialogue_type, dialogue in dialogues.items():
        output_dir_path = os.path.join(output_base_path, document_name)
        os.makedirs(output_dir_path, exist_ok=True)
        with open(os.path.join(output_dir_path, f"{dialogue_type}.json"), "w") as file:
            json.dump(dialogue, file, indent=4)


if __name__ == "__main__":
    test_documents(test_dir_path="test_documents/")
