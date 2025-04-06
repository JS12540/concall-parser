from concall_parser.extractors.analyst_dicussion import (
    AnalystDiscussionExtractor,
)
from concall_parser.extractors.commentary import CommentaryExtractor
from concall_parser.extractors.company import CompanyNameExtractor
from concall_parser.extractors.dialogue_extractor import DialogueExtractor
from concall_parser.extractors.management import ManagementExtractor


class ConcallParser:
    """Parses the conference call transcript."""

    def __init__(self):
        self.company_extractor = CompanyNameExtractor()
        self.management_extractor = ManagementExtractor()
        self.commentary_extractor = CommentaryExtractor()
        self.analyst_extractor = AnalystDiscussionExtractor()
        self.dialogue_extractor = DialogueExtractor()

    def extract_company_name(self, text: str) -> str:
        """Extracts the company name from the text."""
        return self.company_extractor.extract(text)

    def extract_management_team(self, text: str) -> dict:
        """Extracts the management team from the text."""
        return self.management_extractor.extract(text)

    def extract_commentary(self, transcript: dict[int, str]) -> list:
        """Extracts commentary from the input."""
        dialogues = self.dialogue_extractor.extract(transcript)
        return dialogues["commentary_and_future_outlook"]

    def extract_analyst_discussion(self, transcript: dict[int, str]) -> dict:
        """Extracts analyst discussion from the input."""
        dialogues = self.dialogue_extractor.extract(transcript)
        return dialogues["analyst_discussion"]

    def extract_all(
        self, transcript: dict[int, str], first_page_text: str | None = None
    ) -> dict:
        """Extracts all information from the input."""
        dialogues = self.dialogue_extractor.extract(transcript)
        return {
            "company_name": self.company_extractor.extract(
                first_page_text or ""
            ),
            "management_team": self.management_extractor.extract(
                first_page_text or ""
            ),
            "commentary_and_future_outlook": dialogues[
                "commentary_and_future_outlook"
            ],
            "analyst_discussion": dialogues["analyst_discussion"],
            "end": dialogues["end"],
        }
