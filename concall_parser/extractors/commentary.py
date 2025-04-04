from concall_parser.base_parser import BaseExtractor
from concall_parser.utils.cleaner import clean_text


class CommentaryExtractor(BaseExtractor):
    """Extracts commentary from the input."""

    def extract(self, dialogues: list) -> list:
        """Extracts commentary from the input."""
        return [
            {"speaker": d["speaker"], "dialogue": clean_text(d["dialogue"])}
            for d in dialogues
            if d.get("intent") == "opening"
        ]
