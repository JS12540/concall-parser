import json
import os

import pdfplumber

from backend.log_config import logger


def get_document_transcript(filepath: str) -> dict[int, str]:
    """Extracts text of a pdf document.

    Args:
        filepath: Path to the pdf file whose text needs to be extracted.

    Returns:
        transcript: Dictionary of page number, page text pair.
    """
    transcript = dict()
    try:
        with pdfplumber.open(filepath) as pdf:
            logger.debug("Loaded document %s", filepath)
            for page in pdf.pages:
                transcript[str(page.page_number)] = page.extract_text()
    except Exception:
        logger.exception("Could not extract transcript for file with path %s", filepath)
    return transcript


def save_output(
    dialogues: dict, document_name: str, output_base_path: str = "output"
) -> None:
    """Save dialogues to JSON files in the specified output path.

    Takes the dialogues dict as input, splits it into three parts, each saved
    as a json file in a common directory with path output_base_path/document_name.

    Args:
        dialogues (dict): Extracted dialogues, speaker-transcript pairs.
        output_base_path (str): Path to directory in which outputs are to be saved.
        document_name (str): Name of the file being parsed, corresponds to company name for now.
    """
    for dialogue_type, dialogue in dialogues.items():
        output_dir_path = os.path.join(output_base_path, document_name)
        os.makedirs(output_dir_path, exist_ok=True)
        with open(os.path.join(output_dir_path, f"{dialogue_type}.json"), "w") as file:
            json.dump(dialogue, file, indent=4)


def save_transcript(
    transcript: dict,
    document_path: str,
    output_base_path: str = "raw_transcript",
) -> None:
    """Save the extracted text to a file.

    Takes in a transcript, saves it to a text file in a directory for human verification.

    Args:
        transcript (dict): Page number, page text pair extracted using pdfplumber.
        document_path (str): Path of file being processed, corresponds to company name.
        output_base_path (str): Path of directory where transcripts are to be saved.
    """
    try:
        document_name = os.path.basename(document_path)[:-4] # remove the .pdf
        output_dir_path = os.path.join(output_base_path, document_name)
        os.makedirs(output_base_path, exist_ok=True)
        with open(f"{output_dir_path}.txt", "w") as file:
            for _, text in transcript.items():
                file.write(text)
                file.write("\n\n")
        logger.info("Saved transcript text to file\n")
    except Exception:
        logger.exception('Could not save document transcript')
