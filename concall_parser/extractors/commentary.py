from concall_parser.utils.cleaner import clean_text
from concall_parser.base_parser import BaseExtractor

class CommentaryExtractor(BaseExtractor):
    def extract(self, dialogues: list) -> list:
        return [
            {"speaker": d["speaker"], "dialogue": clean_text(d["dialogue"])}
            for d in dialogues if d.get("intent") == "opening"
        ]
