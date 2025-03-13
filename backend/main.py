import json
import re

import pdfplumber

from backend.agents.classify_moderator_intent import ClassifyModeratorIntent
from backend.agents.extract_management import ExtractManagement

# Path to the uploaded PDF
pdf_path = "d9791ed3-f139-4c06-8750-510adfa779eb.pdf"

page_numbers = {}

with pdfplumber.open(pdf_path) as pdf:
    page_number = 1
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            page_numbers[page_number] = text
            page_number += 1


class ConferenceCallParser:
    """Class to parse conference call transcript."""

    def __init__(self):
        self.speaker_pattern = re.compile(
            r"(?P<speaker>[A-Za-z\s]+):\s*(?P<dialogue>(?:.*(?:\n(?![A-Za-z\s]+:).*)*)*)",
            re.MULTILINE,
        )
        self.current_analyst = None

    def clean_text(self, text: str) -> str:
        """Remove extra spaces, normalize case, and ensure consistency."""
        return re.sub(r"\s+", " ", text).strip().lower()

    def extract_company_name(self, text: str) -> str:
        """Extract company name that appears after 'Yours faithfully'."""
        pattern = r"Yours faithfully,\s*For\s*(.*?)\s*_"
        match = re.search(pattern, text)
        return match.group(1) if match else "Company name not found."

    def extract_management_team(self, text) -> list[dict[str, str]]:
        """Extract management team members and their designations."""
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

        for page_number, text in transcript_dict.items():
            if page_number < 3:
                continue

            matches = self.speaker_pattern.finditer(text)
            for match in matches:
                speaker = match.group("speaker").strip()
                dialogue = match.group("dialogue")
                print(f"Speaker: {speaker}, Dialogue: {dialogue}")
                if speaker == "Moderator":
                    print(
                        "Moderator statement found, giving it for classification"
                    )
                    response = ClassifyModeratorIntent.process(
                        dialogue=dialogue
                    )
                    response = json.loads(response)
                    print(f"Response from Moderator classifier: {response}")
                    intent = response["intent"]
                    if intent == "new_analyst_start":
                        analyst_name = response["analyst_name"]
                        analyst_company = response["analyst_company"]
                        self.current_analyst = analyst_name
                        print(f"Current analyst set to: {self.current_analyst}")
                        dialogues["analyst_discussion"][
                            self.current_analyst
                        ] = {"analyst_company": analyst_company, "dialogue": []}
                    print(
                        "Skipping moderator statement as it is not needed anymore"
                    )
                    continue
                # ! error: intent referenced before assignment, did the assignment did not happen as
                #  expected?
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


def parse_conference_call(transcript_dict: dict[int, str]) -> dict:
    """Main function to parse and print conference call information."""
    parser = ConferenceCallParser()
    company_name = ""
    management_team = {}

    # Extract company name and management team
    for page_number, text in transcript_dict.items():
        if page_number == 1:
            company_name = parser.extract_company_name(text=text)
        elif page_number == 2:
            management_team = parser.extract_management_team(text=text)
        else:
            break

    print(f"Company Name: {company_name}")
    print("Management Team:")
    for name, designation in management_team.items():
        print(f"Name: {name}, Designation: {designation}")

    # Extract dialogues
    dialogues = parser.extract_dialogues(transcript_dict)

    print(json.dumps(dialogues, indent=4))


# Example usage
if __name__ == "__main__":
    parse_conference_call(page_numbers)
