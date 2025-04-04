from concall_parser.utils.cleaner import clean_text
from concall_parser.base_parser import BaseExtractor

class AnalystDiscussionExtractor(BaseExtractor):
    def extract(self, discussion: dict) -> dict:
        for analyst, content in discussion.items():
            content["dialogue"] = [
                {"speaker": d["speaker"], "dialogue": clean_text(d["dialogue"])}
                for d in content["dialogue"]
            ]
        return discussion
