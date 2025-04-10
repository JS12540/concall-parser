import json

from concall_parser.agents.extraction import ExtractManagement
from concall_parser.base_parser import BaseExtractor
from concall_parser.log_config import logger


class CompanyAndManagementExtractor(BaseExtractor):
    """Extracts management team from the input."""

    def extract(self, text: str, groq_model: str) -> dict:
        """Extracts management team from the input."""
        try:
            response = ExtractManagement.process(
                page_text=text, groq_model=groq_model
            )
            return json.loads(response)
        except Exception:
            logger.exception("Failed to extract management team.")
            return {}
