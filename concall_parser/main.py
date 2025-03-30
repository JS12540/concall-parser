import json
import re

from concall_parser.parser import ConferenceCallParser
from concall_parser.log_config import logger
import pdfplumber


def extract_management_team_from_text(text: str, management_team: dict) -> dict:
    """Extract management dialogues from text until the next speaker."""
    extracted_dialogues = {}  # To store extracted dialogues

    # Create regex pattern to find each management member and what they spoke
    # extracts all management name and speech pairs in a given text
    # ? but what if some other guy talks in between? is this handled beforehand?
    management_pattern = (
        r"("
        + "|".join(re.escape(name) for name in management_team.keys())
        + r")(.*?)(?=(?:"
        + "|".join(re.escape(name) for name in management_team.keys())
        + r")|$)"
    )
    # ? what does finditer, group and dotall do
    matches = re.finditer(management_pattern, text, re.DOTALL)

    # ? what is the input and output here - how are dialogues extracted? i need logs to understand
    for match in matches:
        speaker = match.group(1)
        dialogue = match.group(2).strip()
        extracted_dialogues[speaker] = dialogue

    return extracted_dialogues


def parse_conference_call(transcript_dict: dict[int, str]) -> dict:
    """Main function to parse and print conference call information."""
    parser = ConferenceCallParser()
    management_team = {}
    extracted_text = ""
    # Extract company name and management team
    # TODO: need to add an extra if in page 2,
    # else case should handle case like reliance (no names given)
    for page_number, text in transcript_dict.items():
        if page_number == 1:
            extracted_text += text
            # generalize for pages 1 and 2?
            if "MANAGEMENT" in text:
                # If first page contains management info, remove from doc, parse it
                logger.debug(f"Page number popped:{page_number}")
                transcript_dict.pop(page_number)
                break
        if page_number == 2:
            # add check for management here, if not present, assume reliance case
            if "MANAGEMENT" in text:
                logger.debug(f"Page number popped:{page_number}")
                extracted_text += text
                transcript_dict.pop(1)
                transcript_dict.pop(page_number)
                break
            else:
                break

    management_team = parser.extract_management_team(text=extracted_text)

    logger.debug(management_team)

    # Check if moderator exists
    # Can't this be put inside that if? are we using this later?
    moderator_found = any(
        "Moderator:" in text for text in transcript_dict.values()
    )

    if moderator_found:
        # Extract dialogues
        dialogues = parser.extract_dialogues(transcript_dict)
    else:
        # ?why do we do things differently if the moderator is not present?
        logger.debug("No moderator found, extracting management team from text")
        dialogues = extract_management_team_from_text(
            " ".join(transcript_dict.values()), management_team
        )

    logger.info(json.dumps(dialogues, indent=4) + "\n\n")
    return dialogues

def get_document_transcript(filepath: str):
    """Creates a text transcript of the given pdf document.

    Params:
        - filepath (str): Path to pdf file being processed.

    Returns:
        - transcript (dict): Page number, page text pair as extracted using pdfplumber.
    """
    transcript = {}
    try:
        with pdfplumber.open(filepath) as pdf:
            logger.debug("Loaded document")
            page_number = 1
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    transcript[page_number] = text
                    page_number += 1
        return transcript
    except Exception:
        logger.exception("Could not load file %s", filepath)

if __name__ == "__main__":
    transcript = get_document_transcript(
        filepath=r"test_documents\ambuja_cement.pdf"
    )

    dialogues = parse_conference_call(transcript_dict=transcript)
    print(dialogues, indent=4)
