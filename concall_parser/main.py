import json
import re

from concall_parser.agents.check_moderator import CheckModerator
from concall_parser.log_config import logger
from concall_parser.parser import ConcallParser


def extract_management_team_from_text(text: str, management_team: dict) -> dict:
    """Extract management dialogues from text until the next speaker."""
    extracted_dialogues = {}

    # Create regex pattern to find each management member and what they spoke
    # extracts all management name and speech pairs in a given text
    management_pattern = (
        r"("
        + "|".join(re.escape(name) for name in management_team.keys())
        + r")(.*?)(?=(?:"
        + "|".join(re.escape(name) for name in management_team.keys())
        + r")|$)"
    )
    matches = re.finditer(management_pattern, text, re.DOTALL)

    for match in matches:
        speaker = match.group(1)
        dialogue = match.group(2).strip()
        extracted_dialogues[speaker] = dialogue

    return extracted_dialogues


def parse_conference_call(transcript: dict[int, str]) -> dict:
    """Main function to parse and print conference call information."""
    parser = ConcallParser()
    # Extract company name and management team
    management_team, transcript, management_found_page = find_management_names(
        transcript=transcript, parser=parser
    )

    logger.info(f"management_team: {management_team}")

    moderator_found = any("Moderator:" in text for text in transcript.values())

    if moderator_found:
        dialogues = parser.dialogue_extractor.extract(transcript)
    else:
        logger.info("No moderator found, extracting name from text")
        moderator_name = json.loads(
            CheckModerator.process(page_text=transcript[management_found_page + 1])
        )["moderator"].strip()
        logger.info(f"moderator_name: {moderator_name}")

        if moderator_name:
            for page_number, text in transcript.items():
                text = re.sub(rf"{re.escape(moderator_name)}:", "Moderator:", text)
                transcript[page_number] = text
            dialogues = parser.extract_dialogues(transcript)
        else:
            logger.info("No moderator in transcript")
            dialogues = extract_management_team_from_text(
                " ".join(transcript.values()), management_team
            )

    logger.info(json.dumps(dialogues, indent=4) + "\n\n")
    return dialogues


def handle_only_management_case(transcript: dict[str, str]) -> dict[str, list[str]]:
    """Extracts speaker names and their corresponding speeches from the transcript.

    Args:
        transcript: A dictionary where keys are page numbers (as strings) and
            values are extracted text.

    Returns:
        speech_pair: A dictionary mapping speaker names to a list of their spoken segments.
    """
    all_speakers = set()
    speech_pair: dict[str, list[str]] = {}

    for _, text in transcript.items():
        matches = re.findall(
            r"([A-Z]\.\s)?([A-Za-z\s]+):\s(.*?)(?=\s[A-Z]\.?\s?[A-Za-z\s]+:\s|$)",
            text,
            re.DOTALL,
        )

        for initial, name, speech in matches:
            speaker = (
                f"{(initial or '').strip()} {name.strip()}".strip()
            )  # Clean speaker name
            speech = re.sub(r"\n", " ", speech).strip()  # Clean speech text

            if speaker not in all_speakers:
                all_speakers.add(speaker)
                speech_pair[speaker] = []

            speech_pair[speaker].append(speech)

    logger.debug(f"Extracted Speakers: {all_speakers}")
    return speech_pair


def find_management_names(
    transcript: dict[int, str], parser: ConcallParser
) -> tuple[list, dict[int, str]]:
    """Checks if the names of management team are present in the text or not.

    Checks the first three pages if they contain the management team, if not,
    assume apollo case and extract all speakers.

    Passes the page containing name of management back in the first case, names
    of all speakers in the apollo case.

    Args:
        transcript: The page number, page text pair dict extracted from the document.
        parser: ConferenceCallParser object required for text extraction.

    Returns:
        speaker_names: A list of speaker names extracted for the apollo case.
        transcript: Modified transcript dictionary, has a few irrelevant pages removed.
    """
    extracted_text = ""
    management_found_page = 0

    for page_number, text in transcript.items():
        extracted_text += text
        # third condition - handles info edge - edge case
        management_list_conditions = (
            re.search("Management", text, re.IGNORECASE)
            or re.search("Participants", text, re.IGNORECASE)
            or re.search("anagement", text, re.IGNORECASE)
        )
        if management_list_conditions:
            management_found_page = page_number
            logger.info("Found management on page %s", management_found_page)
            break

    # apollo case, ie. no management team given in first few pages
    if management_found_page == 0:
        # get all speakers from text
        logger.info("Found no management list, switching to regex search")
        speakers = handle_only_management_case(transcript=transcript).keys()
        extracted_text = transcript.get(1, "") + "\n" + "\n".join(speakers)
        # pass in the first page(for company name), all extracted speakers separated by \n
        speaker_names = parser.extract_management_team(text=extracted_text)
        return speaker_names, transcript

    # management list found, remove pages till that (irrelevant, do not contain speech)
    for page_number in list(transcript.keys()):
        if page_number <= management_found_page:
            transcript.pop(page_number)

    speaker_names = parser.extract_management_team(text=extracted_text)
    return speaker_names, transcript, management_found_page
