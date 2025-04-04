import json
from concall_parser.agents.extraction import ExtractManagement
from concall_parser.log_config import logger
from concall_parser.base_parser import BaseExtractor

class ManagementExtractor(BaseExtractor):
    def extract(self, text: str) -> dict:
        try:
            response = ExtractManagement.process(page_text=text)
            return json.loads(response)
        except Exception:
            logger.exception("Failed to extract management team.")
            return {}
