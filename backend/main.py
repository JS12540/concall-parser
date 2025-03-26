import json
import re

from backend.agents.classify_moderator_intent import ClassifyModeratorIntent
from backend.agents.extract_management import ExtractManagement
from backend.log_config import logger
from backend.management_fix_no_names import handle_only_management_case
from backend.utils.file_utils import (
    get_document_transcript,
    save_output,
    save_transcript,
)


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

    def extract_management_team(self, text) -> dict[str, str]:
        """Extract management team members and their designations.

        Handles case where names of all management personnel participating in
        call are present on one page using the ExtractManagement agent.
        """
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
        # logger.info("Dialogues: \n\n%s", dialogues)
        logger.info("Extracted dialogues\n\n")
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
    # Extract company name and management team
    management_team, transcript_dict = find_management_names(
        transcript=transcript_dict, parser=parser
    )

    logger.debug(management_team)

    # Check if moderator exists
    # Can't this be put inside that if? are we using this later?
    moderator_found = any("Moderator:" in text for text in transcript_dict.values())

    if moderator_found:
        # Extract dialogues
        dialogues = parser.extract_dialogues(transcript_dict)
    else:
        # two cases: moderator is really not there, or moderator name is used.
        logger.debug("No moderator found, extracting management team from text")
        # TODO: fix case where moderator name is used instead of keyword (llm call)
        
        dialogues = extract_management_team_from_text(
            " ".join(transcript_dict.values()), management_team
        )

    # logger.info(json.dumps(dialogues, indent=4) + "\n\n")
    return dialogues


def find_management_names(
    transcript: dict[int, str], parser: ConferenceCallParser
) -> tuple[list, dict[int, str]]:
    """Checks if the names of management team are present in the text or not.

    Checks the first three pages if they contain the management team, if not,
    assume apollo case and extract all speakers.

    Passes the page containing name of management back in the first case, names
    of all speakers in the apollo case.

    Args:
        transcript: The page number, page text pair dict extracted from the document.
        parser: ConferenceCallParser object required for text extraction.

    Returns:
        speaker_names: A list of speaker names extracted for the apollo case.
        transcript: Modified transcript dictionary, has a few irrelevant pages removed.
    """
    # ? Shouldn't the text we send to the agent just be of the page the
    # management names are on? Why are we saving all in extracted_text?
    extracted_text = ""
    management_found_page = 0

    for page_number, text in transcript.items():
        extracted_text += text
        management_list_conditions = re.search(
            "Management", text, re.IGNORECASE
        ) or re.search("Participants", text, re.IGNORECASE)
        if management_list_conditions:
            management_found_page = page_number
            logger.debug("Found management on page %s", management_found_page)
            break

    # apollo case, ie. no management list given
    if management_found_page == 0:
        # get all speakers from text
        logger.debug("Found no management list, switching to regex search")
        speakers = handle_only_management_case(transcript=transcript).keys()
        extracted_text = transcript.get(1, "") + "\n" + "\n".join(speakers)
        # pass in the first page(for company name), all extracted speakers separated by \n
        speaker_names = parser.extract_management_team(text=extracted_text)
        return speaker_names, transcript

    # management list found, remove pages till that (irrelevant, do not contain speech)
    transcript = {k: v for k, v in transcript.items() if k > management_found_page}

    speaker_names = parser.extract_management_team(text=extracted_text)
    return speaker_names, transcript


if __name__ == "__main__":
    document_path = r"test_documents/ambuja_cement.pdf"
    transcript = get_document_transcript(filepath=document_path)
    save_transcript(transcript, document_path)

    dialogues = parse_conference_call(transcript_dict=transcript)
    logger.info("Parsed dialogues for %s \n\n", document_path)
    save_output(dialogues, document_path, "output")
