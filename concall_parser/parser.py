from concall_parser.config import get_groq_api_key, get_groq_model
from concall_parser.extractors.dialogue_extractor import DialogueExtractor
from concall_parser.extractors.management import CompanyAndManagementExtractor
from concall_parser.extractors.management_case_extractor import (
    ManagementCaseExtractor,
)
from concall_parser.utils.file_utils import (
    get_document_transcript,
    get_transcript_from_link,
)


class ConcallParser:
    """Parses the conference call transcript."""

    def __init__(self, path: str = None, link: str = None):
        self.transcript = self._get_document_transcript(
            filepath=path, link=link
        )
        self.groq_api_key = get_groq_api_key()
        self.groq_model = get_groq_model()

        self.company_and_management_extractor = CompanyAndManagementExtractor()
        self.dialogue_extractor = DialogueExtractor()
        self.management_case_extractor = ManagementCaseExtractor()

    def _get_document_transcript(
        self, filepath: str, link: str
    ) -> dict[int, str]:
        """Extracts text of a pdf document.

        Takes in a filepath (locally stored document) or link (online doc) to extract document
        transcript.

        Args:
            filepath: Path to the pdf file whose text needs to be extracted.
            link: Link to concall pdf.

        Returns:
            transcript: Dictionary of page number, page text pair.

        Raises:
            Exception in case neither of filepath or link are provided.
        """
        if not (filepath or link):
            raise Exception(
                "Concall source cannot be empty. Provide filepath or link to concall."
            )

        if link:
            self.transcript = get_transcript_from_link(link=link)
        else:
            self.transcript = get_document_transcript(filepath=filepath)
        return self.transcript

    def extract_concall_info(self) -> dict:
        """Extracts company name and management team from the transcript.

        Args:
            None

        Returns:
            dict: Company name and management team as a dictionary.
        """
        extracted_text = ""
        for page_number, text in self.transcript.items():
            if page_number <= 2:
                extracted_text += text
            else:
                break
        return self.company_and_management_extractor.extract(
            text=extracted_text,
            groq_model=self.groq_model,
        )

    def extract_commentary(self) -> list:
        """Extracts commentary from the input."""
        response = (
            self.dialogue_extractor.extract_commentary_and_future_outlook(
                transcript=self.transcript,
                groq_model=self.groq_model,
            )
        )
        return response

    def handle_only_management_case(self) -> dict[str, list[str]]:
        """Extracts dialogue where moderator is not present."""
        return self.management_case_extractor.extract(self.transcript)

    def extract_analyst_discussion(self) -> dict:
        """Extracts analyst discussion from the input."""
        dialogues = self.dialogue_extractor.extract_dialogues(
            transcript_dict=self.transcript,
            groq_model=self.groq_model,
        )
        return dialogues["analyst_discussion"]

    def extract_all(self) -> dict:
        """Extracts all information from the input."""
        management = self.extract_concall_info()
        commentary = self.extract_commentary()
        analyst = self.extract_analyst_discussion()
        return {
            "concall_info": management,
            "commentary": commentary,
            "analyst": analyst,
        }
