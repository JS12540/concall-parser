import json
import re

import pdfplumber

from backend.agents.classify_moderator_intent import ClassifyModeratorIntent
from backend.agents.extract_management import ExtractManagement

# Path to the uploaded PDF
pdf_path = "d9791ed3-f139-4c06-8750-510adfa779eb.pdf"

speaker_pattern = re.compile(r"(?P<speaker>[A-Za-z\s]+):\s(?P<dialogue>.+)")
analyst_pattern = re.compile(
    r"The next question is from the line of (?P<analyst>.+?) from (?P<company>.+?)\."
)  # noqa


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
            r"(?P<speaker>[A-Za-z\s]+):\s(?P<dialogue>.+)"
        )

    def clean_text(self, text: str) -> str:
        """Remove extra spaces, normalize case, and ensure consistency."""
        return re.sub(r"\s+", " ", text).strip().lower()

    def extract_company_name(self, text: str) -> str:
        """Extract company name that appears after 'Yours faithfully'."""
        pattern = r"Yours faithfully,\s*For\s*(.*?)\s*_"
        match = re.search(pattern, text)
        return match.group(1) if match else "Company name not found"

    def extract_management_team(self, text) -> list[dict[str, str]]:
        """Extract management team members and their designations."""
        response = ExtractManagement.process(page_text=text)
        return response

    def extract_dialogues(self, transcript_dict: dict[int, str]) -> dict:
        """Extract dialogues and classify stages."""
        dialogues = {
            "Commentary_and_Future_Outlook": [],
            "Management_Analyst": {},
            "End": [],
        }
        current_stage = None
        current_analyst = None

        for page_number, text in transcript_dict.items():
            if page_number < 3:
                continue
            lines = text.split("\n")
            for line in lines:
                match = self.speaker_pattern.match(line)
                if match:
                    speaker = match.group("speaker").strip()
                    dialogue = match.group("dialogue").strip()

                    if speaker == "Moderator":
                        intent = ClassifyModeratorIntent.process(dialogue)

                        if intent == "Opening":
                            current_stage = "Commentary_and_Future_Outlook"
                        elif intent == "Analyst Q&A Start":
                            current_stage = "Management_Analyst"

                            # Extract analyst name and company
                            analyst_match = analyst_pattern.search(dialogue)
                            if analyst_match:
                                current_analyst = analyst_match.group("analyst")
                                analyst_company = analyst_match.group("company")

                                if (
                                    current_analyst
                                    not in dialogues["Management_Analyst"]
                                ):
                                    dialogues["Management_Analyst"][
                                        current_analyst
                                    ] = {
                                        "company_name": analyst_company,
                                        "dialogues": [],
                                    }

                        elif intent == "End":
                            current_stage = "End"
                            current_analyst = (
                                None  # End stage, no analyst context
                            )

                    else:
                        if (
                            current_stage == "Management_Analyst"
                            and current_analyst
                        ):
                            dialogues["Management_Analyst"][current_analyst][
                                "dialogues"
                            ].append(dialogue)
                        elif current_stage:
                            dialogues[current_stage].append(dialogue)

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
