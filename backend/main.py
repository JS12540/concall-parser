import json
import re

import pdfplumber

from backend.agents.classify_moderator_intent import ClassifyModeratorIntent
from backend.agents.extract_management import ExtractManagement

# Path to the uploaded PDF
pdf_path = r"test_documents\reliance.pdf"

transcript = {}

# no need of page number dict, iterate over pages list, use page[i].page_number to get page number
with pdfplumber.open(pdf_path) as pdf:
    page_number = 1
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            transcript[page_number] = text
            page_number += 1


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
        response = ExtractManagement.process(page_text=text)
        response = json.loads(response)
        return response

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
                    print(
                        "Skipping moderator statement as it is not needed anymore."
                    )
                else:
                    # analyst or management, get their name
                    first_speaker_match = self.speaker_pattern.search(text)
                    if first_speaker_match:
                        leftover_text = text[
                            : first_speaker_match.start()
                        ].strip()
                        if leftover_text:
                            # Append leftover text (speech) to the last speaker's dialogue
                            print(
                                f"Appending leftover text to {self.last_speaker}"
                            )
                            # TODO: refer to actual data to create model, example
                            if self.current_analyst:
                                dialogues["analyst_discussion"][
                                    self.current_analyst
                                ]["dialogue"][-1]["dialogue"] += (
                                    " " + leftover_text
                                )
                            else:
                                dialogues["commentary_and_future_outlook"][-1][
                                    "dialogue"
                                ] += " " + leftover_text

            # Extract all speakers in that page
            matches = self.speaker_pattern.finditer(text)

            # TODO: why don't we replace self.speaker_pattern.finditer with matches?
            # ? does speaker pattern find speakers in the text or something else?
            if not any(self.speaker_pattern.finditer(text)) and text.strip():
                # If no matches and text exists, append to the last speaker's dialogue
                # this happens when previous speaker (last speaker on previous page) is
                # the only one talking here, it is continuation of speech started on previous page
                print(
                    f"No speaker pattern found, appending text to {self.last_speaker}"
                )
                if self.current_analyst:
                    dialogues["analyst_discussion"][self.current_analyst][
                        "dialogue"
                    ][-1]["dialogue"] += " " + self.clean_text(text)
                else:
                    dialogues["commentary_and_future_outlook"][-1][
                        "dialogue"
                    ] += " " + self.clean_text(text)

            # need explanation of regex here
            for match in matches:
                speaker = match.group("speaker").strip()
                dialogue = match.group("dialogue")
                print(f"Speaker found: {speaker}")
                self.last_speaker = speaker  # Update last speaker

                if speaker == "Moderator":
                    print(
                        "Moderator statement found, giving it for classification"
                    )
                    response = ClassifyModeratorIntent.process(
                        dialogue=dialogue
                    )
                    response = json.loads(response)
                    print(f"\nResponse from Moderator classifier: {response}")
                    intent = response["intent"]
                    if intent == "new_analyst_start":
                        analyst_name = response["analyst_name"]
                        analyst_company = response["analyst_company"]
                        self.current_analyst = analyst_name
                        print(f"Current analyst set to: {self.current_analyst}")
                        dialogues["analyst_discussion"][
                            self.current_analyst
                        ] = {
                            "analyst_company": analyst_company,
                            "dialogue": [],
                        }
                    print(
                        "Skipping moderator statement as it is not needed anymore"
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
                    print(f"Analyst name: {self.current_analyst}")
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

    # Create regex pattern to find each management member
    # TODO: explain what this regex pattern matches, with examples
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
            if "MANAGEMENT" in text:
                print(f"Page number popped:{page_number}")
                transcript_dict.pop(page_number)
                break
        if page_number == 2:
            print(f"Page number popped:{page_number}")
            extracted_text += text
            transcript_dict.pop(1)
            transcript_dict.pop(page_number)
            break

    management_team = parser.extract_management_team(text=extracted_text)

    print(management_team)

    # Check if moderator exists
    # Can't this be put inside that if? are we using this later?
    moderator_found = any(
        "Moderator:" in text for text in transcript_dict.values()
    )

    if moderator_found:
        # Extract dialogues
        dialogues = parser.extract_dialogues(transcript_dict)
    else:
        print("No moderator found, extracting management team from text")
        dialogues = extract_management_team_from_text(
            " ".join(transcript_dict.values()), management_team
        )

    print(json.dumps(dialogues, indent=4))


# Example usage
if __name__ == "__main__":
    parse_conference_call(transcript)
