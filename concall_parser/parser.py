import re
import json
from concall_parser.agents.classify import ClassifyModeratorIntent
from concall_parser.agents.extraction import ExtractManagement
from concall_parser.log_config import logger

class ConferenceCallParser:
    """Class to parse conference call transcript."""

    def __init__(self):
        self.speaker_pattern = re.compile(
            r"(?P<speaker>[A-Za-z\s]+):\s*(?P<dialogue>(?:.*(?:\n(?![A-Za-z\s]+:).*)*)*)",
            re.MULTILINE,
        )
        self.current_analyst = None
        self.last_speaker = None

    def clean_text(self, text: str) -> str:
        """Remove extra spaces, normalize case, and ensure consistency."""
        return re.sub(r"\s+", " ", text).strip().lower()

    def extract_company_name(self, text: str) -> str:
        """Extract company name that appears after 'Yours faithfully'.

        This handles the case where an email is present on the first page of
        the pdf, so the input text should be of the first page.
        """
        pattern = r"Yours faithfully,\s*For\s*(.*?)\s*_"
        match = re.search(pattern, text)
        return match.group(1) if match else "Company name not found"

    def extract_management_team(self, text) -> list[dict[str, str]]:
        """Extract management team members and their designations.

        Handles case where names of all management personnel participating in
        call are present on one page.
        """
        # ! possible issue with type hints in ExtractManagement, need to verify
        try:
            response = ExtractManagement.process(page_text=text)
            response = json.loads(response)
            return response
        except Exception:
            logger.exception("Could not extract management from text")
            return None

    def extract_dialogues(self, transcript_dict: dict[int, str]) -> dict:
        """Extract dialogues and classify stages."""
        dialogues = {
            "commentary_and_future_outlook": [],
            "analyst_discussion": {},
            "end": [],
        }

        # iterate over pages
        for _, text in transcript_dict.items():
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
                                dialogues["commentary_and_future_outlook"][-1][
                                    "dialogue"
                                ] += " " + leftover_text

            # Extract all speakers in that page
            matches = self.speaker_pattern.finditer(text)

            # TODO: why don't we replace self.speaker_pattern.finditer with matches?
            # ? does speaker pattern find speakers in the text or something else?
            if not any(self.speaker_pattern.finditer(text)) and text.strip():
                # If no matches and text exists, append to the last speaker's dialogue
                # this happens when previous speaker (last speaker on previous page) is
                # the only one talking here, it is continuation of speech started on previous page
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

            # need explanation of regex here
            for match in matches:
                speaker = match.group("speaker").strip()
                dialogue = match.group("dialogue")
                logger.debug(f"Speaker found: {speaker}")
                self.last_speaker = speaker  # Update last speaker

                if speaker == "Moderator":
                    logger.debug(
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

                # ? why would intent have a reference before assignment error,
                # what is the text in this case
                if intent == "opening":
                    dialogues["commentary_and_future_outlook"].append(
                        {
                            "speaker": speaker,
                            "dialogue": self.clean_text(dialogue),
                        }
                    )
                elif intent == "new_analyst_start":
                    logger.debug(f"Analyst name: {self.current_analyst}")
                    dialogues["analyst_discussion"][self.current_analyst][
                        "dialogue"
                    ].append(
                        {
                            "speaker": speaker,
                            "dialogue": self.clean_text(dialogue),
                        }
                    )
                elif intent == "end":
                    dialogues["end"].append(
                        {
                            "speaker": speaker,
                            "dialogue": self.clean_text(dialogue),
                        }
                    )

        return dialogues