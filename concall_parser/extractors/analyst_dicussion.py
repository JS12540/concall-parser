from concall_parser.base_parser import BaseExtractor
from concall_parser.utils.cleaner import clean_text


class AnalystDiscussionExtractor(BaseExtractor):
    """Extracts analyst discussion from the input."""

    def extract(self, discussion: dict) -> dict:
        """Extracts analyst discussion from the input."""
        for analyst, content in discussion.items():
            content["dialogue"] = [
                {"speaker": d["speaker"], "dialogue": clean_text(d["dialogue"])}
                for d in content["dialogue"]
            ]
        return discussion
