import os
from enum import Enum

from concall_parser.log_config import logger
from concall_parser.main import parse_conference_call
from concall_parser.utils.file_utils import (
    get_document_transcript,
    save_output,
    save_transcript,
)

FAILED_FILES_LOG = "failed_files.txt"
SUCCESS_FILES_LOG = "success_files.txt"


class TestChoices(Enum):
    """What kind of files to test."""

    TEST_ALL = "all"
    TEST_FAILING = "failing"
    SKIP_SUCCESSFUL = "skip"


def process_single_file(filepath: str, output_path: str):
    """Run a single file and save its output and log."""
    logger.debug(f"Starting testing for {filepath}")
    transcript = get_document_transcript(filepath)
    save_transcript(transcript, output_path, "raw_transcript")

    dialogues = parse_conference_call(transcript=transcript)
    logger.debug("Parsed dialogues\n\n")
    save_output(dialogues, os.path.basename(output_path), "output")


def process_batch(test_dir_path: str, test_all: bool = False):
    """Test all documents in a directory for concall parsing.

    Iterates over all files in a directory containing documents for testing,
    Processes them using the pipeline, saves output to a directory to validate.

    Args:
        test_dir_path (str): Path of directory containing files to test.
        test_all (bool): Flag to toggle testing all documents or only those
            that failed last test.
    """
    error_files = set()
    if os.path.exists(FAILED_FILES_LOG):
        # Use 'with' statement and specify encoding for robustness
        with open(FAILED_FILES_LOG, "r", encoding="utf-8") as file:
            error_files = {line.strip() for line in file if line.strip()}

    files_to_process = set()
    if not test_all:
        files_to_process = error_files
    else:
        # Use os.scandir for efficiency and to filter out directories
        files_to_process = {
            entry.name
            for entry in os.scandir(test_dir_path)
            if entry.is_file()
        }
        # TODO: make standard testing methods
        # The original code had a commented section for skipping successful files.
        # If that functionality is desired, it would be implemented here.
        # if os.path.exists(SUCCESS_FILES_LOG):
        #     with open(SUCCESS_FILES_LOG, "r", encoding="utf-8") as file:
        #         successful_files = {line.strip() for line in file if line.strip()}
        #     files_to_process -= successful_files

    # Sort files for consistent processing order, useful for debugging and reproducibility
    files_to_process_sorted = sorted(files_to_process)

    # Use 'with' statements for log files to ensure they are properly closed
    with (
        open(FAILED_FILES_LOG, "w", encoding="utf-8") as failed_log,
        open(SUCCESS_FILES_LOG, "w", encoding="utf-8") as successful_log,
    ):
        for path in files_to_process_sorted:
            filepath = os.path.join(test_dir_path, path)

            # Double-check if the path points to an actual file
            if not os.path.isfile(filepath):
                logger.warning(f"Skipping non-file entry: {filepath}")
                failed_log.write(path + "\n")  # Log non-files as failed to prevent re-attempting
                continue

            try:
                logger.info(f"Testing {path}")
                process_single_file(filepath, path)
                successful_log.write(path + "\n")
            except Exception:  # Catching bare Exception is generally discouraged but kept for original intent
                failed_log.write(path + "\n")
                logger.exception(f"Error while processing file {path}")
                continue


if __name__ == "__main__":
    process_single_file('test_documents/ambuja_cement.pdf', 'ambuja_cement')
    # process_batch("test_documents", test_all=True)
