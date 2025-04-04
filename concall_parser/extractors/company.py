import re

from concall_parser.base_parser import BaseExtractor


class CompanyNameExtractor(BaseExtractor):
    """Extracts the company name from the text."""

    def extract(self, text: str) -> str:
        """Extracts the company name from the text."""
        pattern = r"Yours faithfully,\s*For\s*(.*?)\s*_"
        match = re.search(pattern, text)
        return match.group(1) if match else "Company name not found"
