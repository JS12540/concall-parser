from collections import defaultdict

from concall_parser.agents.classify import ClassifyModeratorIntent
from concall_parser.utils.cleaner import clean_text


class DialogueExtractor:
    """Extracts dialogue from the input."""

    def __init__(self):
        self.speakers = {
            "moderator": ["moderator", "operator"],
            "management": [],
            "analyst": [],
        }

    def match_speaker(self, speaker: str) -> str:
        """Matches the speaker to one of the three categories."""
        speaker = speaker.lower()
        if any(
            moderator in speaker for moderator in self.speakers["moderator"]
        ):
            return "moderator"
        elif any(analyst in speaker for analyst in self.speakers["analyst"]):
            return "analyst"
        elif any(
            management in speaker for management in self.speakers["management"]
        ):
            return "management"
        return "management"  # default to management if unknown

    def extract(self, transcript: dict[int, str]) -> dict:
        """Extracts dialogue from the input."""
        commentary_and_future_outlook = []
        analyst_discussion = defaultdict(lambda: {"name": "", "dialogue": []})
        end = []

        previous_speaker = ""
        for page in transcript.values():
            try:
                dialogues = eval(page) if isinstance(page, str) else page
            except Exception:
                continue

            for d in dialogues:
                speaker = d.get("speaker", "").strip()
                text = d.get("dialogue", "").strip()
                if not speaker or not text:
                    continue

                clean_dialogue = clean_text(text)
                actual_speaker = self.match_speaker(speaker)

                if actual_speaker == "moderator":
                    intent = ClassifyModeratorIntent.process(
                        dialogue=clean_dialogue
                    ).lower()

                    if "opening" in intent or "future outlook" in intent:
                        commentary_and_future_outlook.append(
                            {"speaker": speaker, "dialogue": clean_dialogue}
                        )
                    elif "end" in intent:
                        end.append(
                            {"speaker": speaker, "dialogue": clean_dialogue}
                        )
                    previous_speaker = "moderator"

                elif actual_speaker == "analyst":
                    if previous_speaker != "analyst":
                        analyst_name = speaker
                    analyst_discussion[analyst_name]["name"] = analyst_name
                    analyst_discussion[analyst_name]["dialogue"].append(
                        {"speaker": speaker, "dialogue": clean_dialogue}
                    )
                    previous_speaker = "analyst"

                elif actual_speaker == "management":
                    if previous_speaker == "analyst":
                        analyst_discussion[analyst_name]["dialogue"].append(
                            {"speaker": speaker, "dialogue": clean_dialogue}
                        )
                    else:
                        commentary_and_future_outlook.append(
                            {"speaker": speaker, "dialogue": clean_dialogue}
                        )
                    previous_speaker = "management"

        return {
            "commentary_and_future_outlook": commentary_and_future_outlook,
            "analyst_discussion": analyst_discussion,
            "end": end,
        }
