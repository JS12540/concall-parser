import re
from dataclasses import dataclass

import pdfplumber

# Path to the uploaded PDF
pdf_path = "d9791ed3-f139-4c06-8750-510adfa779eb.pdf"

# Lists to store extracted information
management_people = []
dialogues = {}

# Patterns to identify key sections
date_pattern = re.compile(
    r"Date:\s*(\d{1,2}\w{2}\s+\w+\s+\d{4})", re.IGNORECASE
)
company_pattern = re.compile(
    r"Yours faithfully,\s*For\s*([A-Z\s]+LIMITED)", re.IGNORECASE
)
management_start_pattern = re.compile(r"MANAGEMENT:", re.IGNORECASE)
management_end_pattern = (
    None  # This will be set dynamically to the company name
)
management_entry_pattern = re.compile(
    r"MR\.\s+([A-Z\s]+)\s+–\s+([A-Z,\s&]+)\s*–\s*([A-Z\s]+LIMITED)",
    re.IGNORECASE,
)
speaker_pattern = re.compile(r"(?P<speaker>[A-Za-z\s]+):\s(?P<dialogue>.+)")

# Variables to store extracted data
conference_date = None
company_name = None
current_speaker = None
inside_management_section = False

page_numbers = {}

with pdfplumber.open(pdf_path) as pdf:
    page_number = 1
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            page_numbers[page_number] = text
            page_number += 1


@dataclass
class DialogueEntry:
    """Dataclass to represent a dialogue entry."""

    speaker: str
    role: str
    content: str


class ConferenceCallParser:
    """Class to parse conference call transcript."""

    def __init__(self, transcript_dict: dict[int, str]):
        self.transcript = transcript_dict
        self.combined_text = "\n".join(transcript_dict.values())

    def extract_company_name(self) -> str:
        """Extract company name that appears after 'Yours faithfully'."""
        pattern = r"Yours faithfully,\s*For\s*(.*?)\s*_"
        match = re.search(pattern, self.combined_text)
        return match.group(1) if match else "Company name not found"

    def extract_management_team(self) -> list[dict[str, str]]:
        """Extract management team members and their designations."""
        management_pattern = r"MR\.\s*(.*?)\s*–\s*(.*?)\s*–\s*(.*?)\s*LIMITED"
        matches = re.finditer(management_pattern, self.combined_text)

        management_team = []
        for match in matches:
            management_team.append(
                {
                    "name": match.group(1),
                    "designation": match.group(2),
                    "company": match.group(3) + " LIMITED",
                }
            )
        return management_team

    def extract_dialogues(self) -> dict[str, list[DialogueEntry]]:
        """Extract and categorize dialogues by participant type."""
        lines = self.combined_text.split("\n")
        dialogues = {"moderator": [], "management": [], "analysts": []}

        current_speaker = ""
        current_role = ""
        current_content = []

        def categorize_speaker(speaker: str) -> str:
            speaker = speaker.strip()
            if speaker == "Moderator":
                return "moderator"
            elif any(
                name["name"] in speaker
                for name in self.extract_management_team()
            ):
                return "management"
            else:
                return "analysts"

        for line in lines:
            # Check for new speaker
            if ":" in line and not line.strip().endswith(":"):
                if current_speaker and current_content:
                    role = current_role
                    content = " ".join(current_content)
                    dialogues[role].append(
                        DialogueEntry(current_speaker, role, content)
                    )
                    current_content = []

                speaker, content = line.split(":", 1)
                current_speaker = speaker.strip()
                current_role = categorize_speaker(current_speaker)
                if content.strip():
                    current_content.append(content.strip())
            elif line.strip() and current_speaker:
                current_content.append(line.strip())

        # Add last dialogue
        if current_speaker and current_content:
            dialogues[current_role].append(
                DialogueEntry(
                    current_speaker, current_role, " ".join(current_content)
                )
            )

        return dialogues


def parse_conference_call(transcript_dict: dict[int, str]) -> None:
    """Main function to parse and print conference call information."""
    parser = ConferenceCallParser(transcript_dict)

    # 1. Extract company name
    company_name = parser.extract_company_name()
    print("\n=== Company Name ===")
    print(company_name)

    # 2. Extract management team
    management_team = parser.extract_management_team()
    print("\n=== Management Team ===")
    for member in management_team:
        print(f"Name: {member['name']}")
        print(f"Designation: {member['designation']}")
        print(f"Company: {member['company']}")
        print()

    # 3. Extract dialogues
    dialogues = parser.extract_dialogues()

    # Print dialogues by category
    for category in ["moderator", "management", "analysts"]:
        print(f"\n=== {category.title()} Dialogues ===")
        for entry in dialogues[category]:
            print(f"\nSpeaker: {entry.speaker}")
            print(f"Content: {entry.content}")
            print("-" * 50)


# Example usage
if __name__ == "__main__":
    parse_conference_call(page_numbers)
