from typing import Optional
from concall_parser.extractors.company import CompanyNameExtractor
from concall_parser.extractors.management import ManagementExtractor
from concall_parser.extractors.commentary import CommentaryExtractor
from concall_parser.extractors.analyst_dicussion import AnalystDiscussionExtractor
from concall_parser.extractors.dialogue_extractor import DialogueExtractor

class ConferenceCallParser:
    def __init__(self):
        self.company_extractor = CompanyNameExtractor()
        self.management_extractor = ManagementExtractor()
        self.commentary_extractor = CommentaryExtractor()
        self.analyst_extractor = AnalystDiscussionExtractor()
        self.dialogue_extractor = DialogueExtractor()

    def extract_company_name(self, text: str) -> str:
        return self.company_extractor.extract(text)

    def extract_management_team(self, text: str) -> dict:
        return self.management_extractor.extract(text)

    def extract_commentary(self, transcript: dict[int, str]) -> list:
        dialogues = self.dialogue_extractor.extract(transcript)
        return dialogues["commentary_and_future_outlook"]

    def extract_analyst_discussion(self, transcript: dict[int, str]) -> dict:
        dialogues = self.dialogue_extractor.extract(transcript)
        return dialogues["analyst_discussion"]

    def extract_all(self, transcript: dict[int, str], first_page_text: Optional[str] = None) -> dict:
        dialogues = self.dialogue_extractor.extract(transcript)
        return {
            "company_name": self.company_extractor.extract(first_page_text or ""),
            "management_team": self.management_extractor.extract(first_page_text or ""),
            "commentary_and_future_outlook": dialogues["commentary_and_future_outlook"],
            "analyst_discussion": dialogues["analyst_discussion"],
            "end": dialogues["end"]
        }
