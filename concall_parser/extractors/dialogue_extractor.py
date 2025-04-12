import json
import re

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
        self, transcript: dict[int, str], groq_model: str
    ) -> dict:
        """Extracts commentary and future outlook from the input."""
        dialogues = {
            "commentary_and_future_outlook": [],
            "analyst_discussion": {},
            "end": [],
        }
        intent = None
        for page_number, text in transcript.items():
            logger.info(f"Processing page {page_number}")
            if self.last_speaker:
                if self.last_speaker == "Moderator":
                    logger.info(
                        "Skipping moderator statement as it is not needed anymore."
                    )
            else:
                first_speaker_match = self.speaker_pattern.search(text)
                if first_speaker_match:
                    leftover_text = text[: first_speaker_match.start()].strip()
                    if leftover_text:
                        logger.info(
                            f"Appending leftover text to {self.last_speaker}"
                        )
                        if self.current_analyst:
                            dialogues["analyst_discussion"][
                                self.current_analyst
                            ]["dialogue"][-1]["dialogue"] += " " + leftover_text
                        else:
                            dialogues["commentary_and_future_outlook"][-1][
                                "dialogue"
                            ] += " " + leftover_text

            matches = self.speaker_pattern.finditer(text)

            for match in matches:
                speaker = match.group("speaker").strip()
                dialogue = match.group("dialogue").strip()
                logger.info(f"Speaker found: {speaker}")
                self.last_speaker = speaker

                if speaker == "Moderator":
                    logger.info(
                        "Moderator statement found, giving it for classification"
                    )
                    response = ClassifyModeratorIntent.process(
                        dialogue=dialogue,
                        groq_model=groq_model,
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
                    continue

                if intent == "opening":
                    dialogues["commentary_and_future_outlook"].append(
                        {
                            "speaker": speaker,
                            "dialogue": clean_text(dialogue),
                        }
                    )
                else:
                    return dialogues["commentary_and_future_outlook"]

    def extract_dialogues(
        self, transcript_dict: dict[int, str], groq_model: str
    ) -> dict:
        """Extract dialogues and classify stages."""
        dialogues = {
            "commentary_and_future_outlook": [],
            "analyst_discussion": {},
            "end": [],
        }
        intent = None

        for page_number, text in transcript_dict.items():
            # Add leftover text before speaker pattern to last speaker
            # If not first page of concall
            if self.last_speaker:
                if self.last_speaker == "Moderator":
                    logger.debug(
                        "Skipping moderator statement as it is not needed anymore."
                    )
                else:
                    # analyst or management, get their name
                    first_speaker_match = self.speaker_pattern.search(text)
                    if first_speaker_match:
                        leftover_text = text[
                            : first_speaker_match.start()
                        ].strip()
                        if leftover_text:
                            # Append leftover text (speech) to the last speaker's dialogue
                            logger.debug(
                                f"Appending leftover text to {self.last_speaker}"
                            )
                            # TODO: refer to actual data to create model, example
                            if self.current_analyst:
                                dialogues["analyst_discussion"][
                                    self.current_analyst
                                ]["dialogue"][-1]["dialogue"] += (
                                    " " + leftover_text
                                )
                            else:
                                if (
                                    dialogues["commentary_and_future_outlook"]
                                    != []
                                ):
                                    dialogues["commentary_and_future_outlook"][
                                        -1
                                    ]["dialogue"] += " " + leftover_text

            matches = self.speaker_pattern.finditer(text)

            if not any(self.speaker_pattern.finditer(text)) and text.strip():
                logger.debug(
                    f"No speaker pattern found, appending text to {self.last_speaker}"
                )
                if self.current_analyst:
                    dialogues["analyst_discussion"][self.current_analyst][
                        "dialogue"
                    ][-1]["dialogue"] += " " + self.clean_text(text)
                else:
                    dialogues["commentary_and_future_outlook"][-1][
                        "dialogue"
                    ] += " " + self.clean_text(text)

            for match in matches:
                speaker = match.group("speaker").strip()
                dialogue = match.group("dialogue")
                logger.debug(f"Speaker found: {speaker}")
                self.last_speaker = speaker

                if speaker == "Moderator":
                    logger.debug(
                        "Moderator statement found, giving it for classification"
                    )
                    response = ClassifyModeratorIntent.process(
                        dialogue=dialogue,
                        groq_model=groq_model,
                    )
                    response = json.loads(response)
                    logger.info(
                        f"Response from Moderator classifier: {response}"
                    )
                    intent = response["intent"]
                    if intent == "new_analyst_start":
                        analyst_name = response["analyst_name"]
                        analyst_company = response["analyst_company"]
                        self.current_analyst = analyst_name
                        logger.debug(
                            f"Current analyst set to: {self.current_analyst}"
                        )
                        dialogues["analyst_discussion"][
                            self.current_analyst
                        ] = {
                            "analyst_company": analyst_company,
                            "dialogue": [],
                        }
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
                elif intent == "new_analyst_start":
                    logger.debug(f"Analyst name: {self.current_analyst}")
                    dialogues["analyst_discussion"][self.current_analyst][
                        "dialogue"
                    ].append(
                        {
                            "speaker": speaker,
                            "dialogue": clean_text(dialogue),
                        }
                    )
                elif intent == "end":
                    dialogues["end"].append(
                        {
                            "speaker": speaker,
                            "dialogue": clean_text(dialogue),
                        }
                    )

        return dialogues
