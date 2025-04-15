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

    def extract_commentary_and_future_outlook(
        self, transcript: dict[int, str], groq_model: str
    ) -> dict:
        """Extracts commentary and future outlook from the input."""
        last_speaker = None
        dialogues = {
            "commentary_and_future_outlook": [],
            "analyst_discussion": {},
            "end": [],
        }
        intent = None
        current_analyst = None

        for page_number, text in transcript.items():
            print(f"Processing page {page_number}")
            if last_speaker:
                logger.info(f"Checking for leftover text for {last_speaker}")
                if last_speaker == "Moderator":
                    logger.info(
                        "Skipping moderator statement as it is not needed anymore."
                    )
                else:
                    first_speaker_match = self.speaker_pattern.search(text)
                    if first_speaker_match:
                        leftover_text = text[
                            : first_speaker_match.start()
                        ].strip()
                        if leftover_text and last_speaker is not None:
                            if current_analyst:
                                dialogues["analyst_discussion"][
                                    current_analyst
                                ]["dialogue"][-1]["dialogue"] += (
                                    " " + leftover_text
                                )
                            else:
                                if (
                                    len(
                                        dialogues[
                                            "commentary_and_future_outlook"
                                        ]
                                    )
                                    > 0
                                ):
                                    dialogues["commentary_and_future_outlook"][
                                        -1
                                    ]["dialogue"] += " " + leftover_text
                    else:
                        logger.info(
                            f"No matches found, appending leftover text to {last_speaker}"
                        )
                        if current_analyst:
                            dialogues["analyst_discussion"][current_analyst][
                                "dialogue"
                            ][-1]["dialogue"] += " " + text
                        else:
                            if (
                                len(dialogues["commentary_and_future_outlook"])
                                > 0
                            ):
                                dialogues["commentary_and_future_outlook"][-1][
                                    "dialogue"
                                ] += " " + text
                        continue

            matches = self.speaker_pattern.finditer(text)

            for match in matches:
                speaker = match.group("speaker").strip()
                dialogue = match.group("dialogue").strip()
                logger.info(f"Speaker found: {speaker}")
                last_speaker = speaker

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
        last_speaker = None
        current_analyst = None

        for page_number, text in transcript_dict.items():
            # Add leftover text before speaker pattern to last speaker
            # If not first page of concall
            if last_speaker:
                logger.info(f"Checking for leftover text for {last_speaker}")
                if last_speaker == "Moderator":
                    logger.debug(
                        "Skipping moderator statement as it is not needed anymore."
                    )
                else:
                    first_speaker_match = self.speaker_pattern.search(text)
                    if first_speaker_match:
                        leftover_text = text[
                            : first_speaker_match.start()
                        ].strip()
                        if leftover_text:
                            logger.info(
                                f"Appending leftover text to {last_speaker}"
                            )
                            # TODO: refer to actual data to create model, example
                            if current_analyst:
                                dialogues["analyst_discussion"][
                                    current_analyst
                                ]["dialogue"][-1]["dialogue"] += (
                                    " " + leftover_text
                                )
                            else:
                                if (
                                    len(
                                        dialogues[
                                            "commentary_and_future_outlook"
                                        ]
                                    )
                                    > 0
                                ):
                                    dialogues["commentary_and_future_outlook"][
                                        -1
                                    ]["dialogue"] += " " + clean_text(
                                        leftover_text
                                    )
                    else:
                        logger.info(
                            "No matches found, appending leftover text to last speaker"
                        )
                        if current_analyst:
                            dialogues["analyst_discussion"][current_analyst][
                                "dialogue"
                            ][-1]["dialogue"] += " " + clean_text(leftover_text)
                        else:
                            if (
                                len(dialogues["commentary_and_future_outlook"])
                                > 0
                            ):
                                dialogues["commentary_and_future_outlook"][-1][
                                    "dialogue"
                                ] += " " + clean_text(leftover_text)

            matches = self.speaker_pattern.finditer(text)

            if not any(self.speaker_pattern.finditer(text)) and text.strip():
                logger.debug(
                    f"No speaker pattern found, appending text to {last_speaker}"
                )
                if current_analyst:
                    dialogues["analyst_discussion"][current_analyst][
                        "dialogue"
                    ][-1]["dialogue"] += " " + clean_text(text)
                else:
                    dialogues["commentary_and_future_outlook"][-1][
                        "dialogue"
                    ] += " " + clean_text(text)

            for match in matches:
                speaker = match.group("speaker").strip()
                dialogue = match.group("dialogue")
                logger.debug(f"Speaker found: {speaker}")
                last_speaker = speaker

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
                        current_analyst = analyst_name
                        logger.debug(
                            f"Current analyst set to: {current_analyst}"
                        )
                        dialogues["analyst_discussion"][current_analyst] = {
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
                    logger.debug(f"Analyst name: {current_analyst}")
                    dialogues["analyst_discussion"][current_analyst][
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
