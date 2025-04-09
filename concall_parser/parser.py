import pdfplumber

from concall_parser.extractors.analyst_dicussion import (
    AnalystDiscussionExtractor,
)
from concall_parser.extractors.commentary import CommentaryExtractor
from concall_parser.extractors.dialogue_extractor import DialogueExtractor
from concall_parser.extractors.management import CompanyAndManagementExtractor
from concall_parser.log_config import logger


class ConcallParser:
    """Parses the conference call transcript."""

    def __init__(self):
        self.company_and_management_extractor = CompanyAndManagementExtractor()
        self.commentary_extractor = CommentaryExtractor()
        self.analyst_extractor = AnalystDiscussionExtractor()
        self.dialogue_extractor = DialogueExtractor()

    def get_document_transcript(self, filepath: str) -> dict[int, str]:
        """Extracts text of a pdf document.

        Args:
            filepath: Path to the pdf file whose text needs to be extracted.

        Returns:
            transcript: Dictionary of page number, page text pair.
        """
        transcript = {}
        try:
            with pdfplumber.open(filepath) as pdf:
                logger.debug("Loaded document")
                page_number = 1
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        transcript[page_number] = text
                        page_number += 1
            return transcript
        except Exception:
            logger.exception("Could not load file %s", filepath)

    def extract_management_team(self, transcript: dict[int, str]) -> dict:
        """Extracts the management team from the text."""
        extracted_text = ""
        for page_number, text in transcript.items():
            if page_number <= 2:
                extracted_text += text
            else:
                break
        return self.company_and_management_extractor.extract(
            text=extracted_text
        )

    def extract_commentary(self, transcript: dict[int, str]) -> list:
        """Extracts commentary from the input."""
        response = (
            self.dialogue_extractor.extract_commentary_and_future_outlook(
                transcript=transcript
            )
        )
        return response

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
