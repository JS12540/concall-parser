import pdfplumber

from concall_parser.config import get_groq_api_key, get_groq_model
from concall_parser.extractors.dialogue_extractor import DialogueExtractor
from concall_parser.extractors.management import CompanyAndManagementExtractor
from concall_parser.log_config import logger


class ConcallParser:
    """Parses the conference call transcript."""

    def __init__(self):
        # Ensure Groq API key is set and get model
        self.groq_api_key = get_groq_api_key()
        self.groq_model = get_groq_model()

        self.company_and_management_extractor = CompanyAndManagementExtractor()
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
            text=extracted_text,
            groq_model=self.groq_model,
        )

    def extract_commentary(self, transcript: dict[int, str]) -> list:
        """Extracts commentary from the input."""
        response = (
            self.dialogue_extractor.extract_commentary_and_future_outlook(
                transcript=transcript,
                groq_model=self.groq_model,
            )
        )
        return response

    def extract_analyst_discussion(self, transcript: dict[int, str]) -> dict:
        """Extracts analyst discussion from the input."""
        dialogues = self.dialogue_extractor.extract_dialogues(
            transcript_dict=transcript,
            groq_model=self.groq_model,
        )
        return dialogues["analyst_discussion"]

    def extract_all(self, transcript: dict[int, str]) -> dict:
        """Extracts all information from the input."""
        management = self.extract_management_team(transcript=transcript)
        commentary = self.extract_commentary(transcript=transcript)
        analyst = self.extract_analyst_discussion(transcript=transcript)
        return {
            "management": management,
            "commentary": commentary,
            "analyst": analyst,
        }
