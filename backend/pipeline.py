import pdfplumber

from .main import parse_conference_call


class ConferenceCallPipeline:
    """Pipeline to process concall documents."""

    def __init__(self) -> None:
        self.doc_text = {}

    def get_document_text(self, document_path:str):
        """Get page number - page text mapping."""
        with pdfplumber.open(document_path) as pdf:
            page_number = 1
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    self.doc_text[page_number] = text
                    page_number += 1

    def parse_text(self):
        """Parse the conference call text."""
        dialogues = parse_conference_call(self.doc_text)
        return dialogues

    def run_pipeline(self, document_path:str):
        """Run the whole pipeline."""
        self.get_document_text(document_path)
        parsed_data = self.parse_text()
        return parsed_data