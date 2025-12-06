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
        except json.JSONDecodeError:
            logger.exception("Failed to decode JSON response from management extraction.")
            return {}
        except Exception:
            logger.exception("An unexpected error occurred during management extraction.")
            return {}
