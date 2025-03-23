import json
import os

from backend.log_config import logger
from backend.main import parse_conference_call
from backend.utils.file_utils import (
    get_document_transcript,
    save_output,
    save_transcript,
)

ERROR_CURSOR_FILE = "failed_files.json"


def test_documents(test_dir_path: str, test_all: bool = False):
    """Test all documents in a directory for concall parsing.

    Iterates over all files in a directory containing documents for testing,
    Processes them using the pipeline, saves output to a directory to validate.

    Args:
        test_dir_path (str): Path of directory containing files to test.
        test_all (bool): Flag to toggle testing all documents or only those
            that failed last test.
    """
    if os.path.exists(ERROR_CURSOR_FILE):
        with open(ERROR_CURSOR_FILE) as file:
            error_files = set(json.load(file))

    if not test_all:
        files_to_test = error_files
    else:
        files_to_test = set(os.listdir(test_dir_path))

    for path in files_to_test:
        try:
            filepath = os.path.join(test_dir_path, path)
            logger.info("Testing %s\n", path)

            transcript = get_document_transcript(filepath)
            save_transcript(transcript, path, "raw_transcript")

            dialogues = parse_conference_call(transcript_dict=transcript)
            save_output(dialogues, os.path.basename(path), "output")

        except Exception:
            error_files.add(path)
            logger.exception(
                "Error while processing file %s",
            )
            continue

    with open(ERROR_CURSOR_FILE, "w") as file:
        json.dump(list(error_files), file)


if __name__ == "__main__":
    test_documents("test_documents", True)
