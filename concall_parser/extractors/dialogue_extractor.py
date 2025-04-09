import json
import re
from collections import defaultdict

from concall_parser.agents.classify import ClassifyModeratorIntent
from concall_parser.log_config import logger
from concall_parser.utils.cleaner import clean_text


class DialogueExtractor:
    """Extracts dialogue from the input."""

    def __init__(self):
        self.speakers = {
            "moderator": ["moderator", "operator"],
            "management": [],
            "analyst": [],
        }
        self.speaker_pattern = re.compile(
            r"(?P<speaker>[A-Za-z\s]+):\s*(?P<dialogue>(?:.*(?:\n(?![A-Za-z\s]+:).*)*)*)",
            re.MULTILINE,
        )
        self.current_analyst = None
        self.last_speaker = None

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

    def extract_commentary_and_future_outlook(
        self, transcript: dict[int, str]
    ) -> dict:
        """Extracts commentary and future outlook from the input."""
        dialogues = {
            "commentary_and_future_outlook": [],
            "analyst_discussion": {},
            "end": [],
        }
        intent = None
        for _, text in transcript.items():
            if self.last_speaker:
                if self.last_speaker == "Moderator":
                    logger.debug(
                        "Skipping moderator statement as it is not needed anymore."
                    )
            else:
                # analyst or management, get their name
                first_speaker_match = self.speaker_pattern.search(text)
                if first_speaker_match:
                    leftover_text = text[: first_speaker_match.start()].strip()
                    if leftover_text:
                        # Append leftover text (speech) to the last speaker's dialogue
                        logger.debug(
                            f"Appending leftover text to {self.last_speaker}"
                        )
                        # TODO: refer to actual data to create model, example
                        if self.current_analyst:
                            dialogues["analyst_discussion"][
                                self.current_analyst
                            ]["dialogue"][-1]["dialogue"] += " " + leftover_text
                        else:
                            dialogues["commentary_and_future_outlook"][-1][
                                "dialogue"
                            ] += " " + leftover_text
            # Extract all speakers in that page
            matches = self.speaker_pattern.finditer(text)
            for match in matches:
                speaker = match.group("speaker").strip()
                dialogue = match.group("dialogue")
                logger.debug(f"Speaker found: {speaker}")
                self.last_speaker = speaker  # Update last speaker

                if speaker == "Moderator":
                    logger.info(
                        "Moderator statement found, giving it for classification"
                    )
                    response = ClassifyModeratorIntent.process(
                        dialogue=dialogue
                    )
                    response = json.loads(response)
                    logger.info(
                        f"Response from Moderator classifier: {response}"
                    )
                    intent = response["intent"]
                    if intent == "new_analyst_start":
                        return dialogues["commentary_and_future_outlook"]

                    logger.debug(
                        "Skipping moderator statement as it is not needed anymore."
                    )
                    continue

                if intent is None:
                    break

                if intent == "opening":
                    dialogues["commentary_and_future_outlook"].append(
                        {
                            "speaker": speaker,
                            "dialogue": clean_text(dialogue),
                        }
                    )
                else:
                    return dialogues["commentary_and_future_outlook"]

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
