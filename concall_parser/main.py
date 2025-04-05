import json
import re

from concall_parser.agents.check_moderator import CheckModerator
from concall_parser.log_config import logger
from concall_parser.management_only import handle_only_management_case
from concall_parser.parser import ConferenceCallParser
from concall_parser.utils.file_utils import (
    get_document_transcript,
    save_output,
    save_transcript,
)


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
    parser = ConferenceCallParser()
    # Extract company name and management team
    management_team, transcript, management_found_page = find_management_names(
        transcript=transcript, parser=parser
    )

    logger.info(f"management_team: {management_team}")

    moderator_found = any("Moderator:" in text for text in transcript.values())

    if moderator_found:
        dialogues = parser.extract_dialogues(transcript)
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


def find_management_names(
    transcript: dict[int, str], parser: ConferenceCallParser
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


if __name__ == "__main__":
    document_path = r"test_documents/tata_motors.pdf"
    logger.info(f"Starting testing for {document_path}")
    try:
        transcript = get_document_transcript(filepath=document_path)
        save_transcript(transcript, document_path)

        dialogues = parse_conference_call(transcript=transcript)
        logger.info("Parsed dialogues for %s \n\n", document_path)
        save_output(dialogues, document_path, "output")
    except Exception:
        logger.exception("Something went really wrong")
