import json
import re

import pdfplumber

from backend.agents.extract_management import ExtractManagement

# Path to the uploaded PDF
pdf_path = "d9791ed3-f139-4c06-8750-510adfa779eb.pdf"

speaker_pattern = re.compile(r"(?P<speaker>[A-Za-z\s]+):\s(?P<dialogue>.+)")

page_numbers = {}

with pdfplumber.open(pdf_path) as pdf:
    page_number = 1
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            page_numbers[page_number] = text
            page_number += 1


# TODO: extract to utils
# TODO: temp text storage for testing, human verification

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

    def extract_dialogues(
        self, transcript_dict: dict[int, str], speakers: list[str]
    ) -> dict:
        """Extract dialogues from the transcript and classify speakers."""
        dialogues = {}
        current_speaker = None

        for page_number, text in transcript_dict.items():
            if page_number < 3:  # Skip first two pages
                continue

            lines = text.split("\n")
            for line in lines:
                match = self.speaker_pattern.match(line)
                if match:
                    speaker = match.group("speaker").strip()
                    dialogue = match.group("dialogue").strip()

                    if speaker not in dialogues:
                        dialogues[speaker] = {"text": "", "pages": []}

                    current_speaker = speaker
                    dialogues[current_speaker]["text"] += " " + dialogue
                    if page_number not in dialogues[current_speaker]["pages"]:
                        dialogues[current_speaker]["pages"].append(page_number)

                elif (
                    current_speaker and line.strip()
                ):  # Continue dialogue for current speaker
                    dialogues[current_speaker]["text"] += " " + line.strip()

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

    print(f"Company Name: {company_name}")
    # Create speakers list
    speakers = ["Moderator"]
    management_team_dict = json.loads(management_team)
    speakers.extend(management_team_dict.keys())

    # Extract dialogues
    dialogues = parser.extract_dialogues(transcript_dict, speakers)

    # Identify analysts and add them to the speaker list
    identified_analysts = [
        spk for spk in dialogues.keys() if spk not in speakers
    ]
    speakers.extend(identified_analysts)

    print(json.dumps(dialogues, indent=4))


# Example usage
if __name__ == "__main__":
    parse_conference_call(page_numbers)
