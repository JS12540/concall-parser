import json
import re

from concall_parser.agents.classify import ClassifyModeratorIntent
from concall_parser.agents.verify_speakers import VerifySpeakerNames
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

    def _get_verified_speakers(
        self, transcript: dict[int, str], groq_model: str
    ):
        """Extracts candidate speakers and verifies them using an LLM."""
        logger.info("Extracting potential speaker candidates...")
        candidates = set()
        try:
            for _, text in transcript.items():
                candidates_page = set(
                    match.group(1).strip()
                    for match in self.speaker_pattern.finditer(text)
                )
                candidates.update(candidates_page)

            if not candidates:
                logger.warning("No potential speaker candidates found.")
                return set(["Moderator"])

            logger.info(
                f"Found {len(candidates)} unique candidates. Verifying names."
            )
            candidates_list = "Candidate:" + json.dumps(list(candidates))
            names = VerifySpeakerNames.process(
                speakers=candidates_list, groq_model=groq_model
            )
            verified_speakers = json.loads(names)["output"]

            if not isinstance(verified_speakers, list):
                raise ValueError("LLM response is not a JSON list.")
            return set(verified_speakers)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode JSON from LLM response: {e}. Response: {names}"
            )
            raise e
        except Exception as e:
            logger.error(f"Error during LLM speaker verification: {e}")
            raise e

    def _build_dynamic_speaker_pattern(self, verified_speakers: set[str]):
        """Builds the regex pattern from a set of verified speaker names."""
        if not verified_speakers:
            logger.error("Cannot build pattern: No verified speakers provided.")
            return

        pattern_string = "|".join(
            re.escape(name) for name in sorted(list(verified_speakers))
        )

        try:
            self.speaker_pattern = re.compile(
                rf"(?P<speaker>{pattern_string}):\s*(?P<dialogue>.(?:\n(?!(?:{pattern_string}):).)*)",
                re.MULTILINE,
            )
            logger.info("Successfully built dynamic speaker pattern.")
            logger.debug(f"Dynamic Pattern: {self.speaker_pattern.pattern}")
        except re.error as e:
            logger.error(f"Failed to compile dynamic regex pattern: {e}")

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
            self.dialogues["analyst_discussion"][current_analyst]["dialogue"][
                -1
            ]["dialogue"] += f" {cleaned}"
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

    def _process_match(
        self, match, groq_model: str, current_analyst: str | None
    ):
        speaker = match.group("speaker").strip()
        dialogue = match.group("dialogue")
        intent = None

        if speaker == "Moderator":
            response = json.loads(
                ClassifyModeratorIntent.process(
                    dialogue=dialogue, groq_model=groq_model
                )
            )
            intent = response["intent"]
            if intent == "new_analyst_start":
                current_analyst = response["analyst_name"]
                self.dialogues["analyst_discussion"][current_analyst] = {
                    "analyst_company": response["analyst_company"],
                    "dialogue": [],
                }
            return intent, current_analyst, None  # Moderator handled

        return intent, current_analyst, (speaker, dialogue)

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

                if speaker == "Moderator":
                    response = json.loads(
                        ClassifyModeratorIntent.process(
                            dialogue=match.group("dialogue"),
                            groq_model=groq_model,
                        )
                    )
                    intent = response["intent"]
                    if intent == "new_analyst_start":
                        return self.dialogues["commentary_and_future_outlook"]
                    continue

                if intent == "opening":
                    self._append_dialogue(
                        speaker,
                        match.group("dialogue"),
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

                if speaker == "Moderator":
                    response = json.loads(
                        ClassifyModeratorIntent.process(
                            dialogue=match.group("dialogue"),
                            groq_model=groq_model,
                        )
                    )
                    intent = response["intent"]
                    if intent == "new_analyst_start":
                        current_analyst = response["analyst_name"]
                        self.dialogues["analyst_discussion"][
                            current_analyst
                        ] = {
                            "analyst_company": response["analyst_company"],
                            "dialogue": [],
                        }
                    continue

                if intent is None:
                    break

                self._append_dialogue(
                    speaker, match.group("dialogue"), intent, current_analyst
                )

        return self.dialogues
