import json
import os

import pdfplumber
from log_config import logger

ERROR_CURSOR_FILE = "failed_files.json"


def save_output(dialogues: dict, output_base_path: str, document_name: str):
    """Save dialogues to JSON files in the specified output path.

    Takes the dialogues dict as input, splits it into three parts, each saved
    as a json file in a common directory with path output_base_path/document_name.

    Params:
        - dialogues (dict): Extracted dialogues, speaker-transcript pairs.
        - output_base_path (str): Path to directory in which outputs are to be saved.
        - document_name (str): Name of the file being parsed, corresponds to company name for now.
    """
    for dialogue_type, dialogue in dialogues.items():
        output_dir_path = os.path.join(output_base_path, document_name)
        os.makedirs(output_dir_path, exist_ok=True)
        with open(
            os.path.join(output_dir_path, f"{dialogue_type}.json"), "w"
        ) as file:
            json.dump(dialogue, file, indent=4)


def save_extracted_text(
    transcript: dict,
    document_name: str,
    output_base_path: str = "raw_transcript",
):
    """Save the extracted text to a file.

    Takes in a transcript, saves it to a text file in a directory for human verification.

    Params:
        - transcript (dict): Page number, page text pair extracted using pdfplumber.
        - document_name (str): Name of file being processed, corresponds to company name.
        - output_base_path (str): Path of directory where transcripts are to be saved.
    """
    output_dir_path = os.path.join(output_base_path, document_name)
    os.makedirs(output_base_path, exist_ok=True)
    with open(f"{output_dir_path}.txt", "w") as file:
        for _, text in transcript.items():
            file.write(text)
            file.write("\n\n")
    logger.info("Saved transcript text to file\n")


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


# def test_documents(test_dir_path: str, test_all: bool = False):
#     """Test all documents in a directory for concall parsing.

#     Iterates over all files in a directory containing documents for testing,
#     Processes them using the pipeline, saves output to a directory to validate.
#     Params:
#         - test_dir_path (str):
#         - test_all (bool): Flag to toggle testing all documents or only those
#             that failed last test.
#     """
#     if os.path.exists(ERROR_CURSOR_FILE):
#         with open(ERROR_CURSOR_FILE) as file:
#             error_files = set(json.load(file))

#     if not test_all:
#         files_to_test = error_files
#     else:
#         files_to_test = set(os.listdir(test_dir_path))

#     for path in files_to_test:
#         try:
#             filepath = os.path.join(test_dir_path, path)
#             logger.info("Testing %s \n", path)

#             transcript = get_document_transcript(filepath)
#             save_extracted_text(transcript, path, "raw_transcript")

#             dialogues = parse_conference_call(transcript_dict=transcript)
#             save_output(dialogues, "output", os.path.basename(path))

#         except Exception:
#             error_files.add(path)
#             logger.exception(
#                 "Error while processing file %s",
#             )
#             continue

#     with open(ERROR_CURSOR_FILE, "w") as file:
#         json.dump(list(error_files), file)
