import json
import re

from concall_parser.agents.classify import ClassifyModeratorIntent
from concall_parser.log_config import logger
from concall_parser.utils.cleaner import clean_text


class DialogueExtractor:
    """Extracts dialogue from the input."""

    def __init__(self):
        self.speaker_pattern = re.compile(
            r"(?P<speaker>[A-Za-z\s]+):\s*(?P<dialogue>(?:.*(?:\n(?![A-Za-z\s]+:).*)*)*)",
            re.MULTILINE,
        )
        self.dialogues = {
            "commentary_and_future_outlook": [],
            "analyst_discussion": {},
            "end": [],
        }
        self.page_number = 0

    def _handle_leftover_text(
        self, text: str, last_speaker: str, current_analyst: str | None
    ):
        first_speaker_match = self.speaker_pattern.search(text)
        if first_speaker_match:
            leftover_text = text[: first_speaker_match.start()].strip()
        else:
            leftover_text = text.strip()

        if not leftover_text or last_speaker == "Moderator":
            return

        cleaned = clean_text(leftover_text)

        if current_analyst:
            analyst_dialogues = self.dialogues["analyst_discussion"][current_analyst][
                "dialogue"
            ]
            if analyst_dialogues:
                analyst_dialogues[-1]["dialogue"] += f" {cleaned}"
            else:
                # If this is the first dialogue for the analyst, treat leftover as their initial statement.
                analyst_dialogues.append(
                    {
                        "speaker": current_analyst,  # Assuming the analyst is speaking
                        "dialogue": cleaned,
                    }
                )
        elif self.dialogues["commentary_and_future_outlook"]:
            self.dialogues["commentary_and_future_outlook"][-1]["dialogue"] += (
                f" {cleaned}"
            )

    def _append_dialogue(
        self,
        speaker: str,
        dialogue: str,
        intent: str,
        current_analyst: str | None,
    ):
        cleaned = clean_text(dialogue)
        if intent == "opening":
            self.dialogues["commentary_and_future_outlook"].append(
                {
                    "speaker": speaker,
                    "dialogue": cleaned,
                }
            )
        elif intent == "new_analyst_start" and current_analyst:
            self.dialogues["analyst_discussion"][current_analyst][
                "dialogue"
            ].append(
                {
                    "speaker": speaker,
                    "dialogue": cleaned,
                }
            )
        elif intent == "end":
            self.dialogues["end"].append(
                {
                    "speaker": speaker,
                    "dialogue": cleaned,
                }
            )

    def _process_moderator_dialogue(
        self, dialogue: str, groq_model: str
    ) -> tuple[str, str | None]:
        """Processes moderator dialogue to classify intent and extract analyst info.
        Updates self.dialogues directly for new analyst discussions.
        """
        response = json.loads(
            ClassifyModeratorIntent.process(
                dialogue=dialogue, groq_model=groq_model
            )
        )
        intent = response["intent"]
        current_analyst = None

        if intent == "new_analyst_start":
            current_analyst = response["analyst_name"]
            analyst_company = response["analyst_company"]
            self.dialogues["analyst_discussion"][current_analyst] = {
                "analyst_company": analyst_company,
                "dialogue": [],
            }
        return intent, current_analyst

    def extract_commentary_and_future_outlook(
        self, transcript: dict[int, str], groq_model: str
    ) -> dict:
        """Extracts commentary and future outlook from the transcript.

        Args:
            transcript (dict[int, str]): The transcript to extract from.
            groq_model (str): The model to use for groq.

        Returns:
            dict: The extracted commentary and future outlook.
        """
        logger.info("Extracting commentary...")
        last_speaker = None
        intent = None
        current_analyst = None

        for page_number, text in transcript.items():
            self.page_number = page_number

            if last_speaker:
                self._handle_leftover_text(text, last_speaker, current_analyst)

            for match in self.speaker_pattern.finditer(text):
                speaker = match.group("speaker").strip()
                last_speaker = speaker
                dialogue_content = match.group("dialogue")

                if speaker == "Moderator":
                    intent, current_analyst = self._process_moderator_dialogue(
                        dialogue_content, groq_model
                    )
                    if intent == "new_analyst_start":
                        return self.dialogues["commentary_and_future_outlook"]
                    continue

                if intent == "opening":
                    self._append_dialogue(
                        speaker,
                        dialogue_content,
                        intent,
                        current_analyst,
                    )
                else:
                    return self.dialogues["commentary_and_future_outlook"]

        return self.dialogues["commentary_and_future_outlook"]

    def extract_dialogues(
        self, transcript_dict: dict[int, str], groq_model: str
    ) -> dict:
        """Extracts dialogues from the transcript.

        Args:
            transcript_dict (dict[int, str]): The transcript to extract from.
            groq_model (str): The model to use for groq.

        Returns:
            dict: The extracted dialogues.
        """
        logger.info("Extracting dialogues...")
        intent = None
        last_speaker = None
        current_analyst = None

        for page_number, text in transcript_dict.items():
            if page_number < self.page_number - 1:
                continue

            if last_speaker:
                self._handle_leftover_text(text, last_speaker, current_analyst)

            for match in self.speaker_pattern.finditer(text):
                speaker = match.group("speaker").strip()
                last_speaker = speaker
                dialogue_content = match.group("dialogue")

                if speaker == "Moderator":
                    intent, current_analyst = self._process_moderator_dialogue(
                        dialogue_content, groq_model
                    )
                    continue

                if intent is None:
                    break

                self._append_dialogue(
                    speaker, dialogue_content, intent, current_analyst
                )

        return self.dialogues
