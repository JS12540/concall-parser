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
    logger.debug("Starting testing for %s", filepath)
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
    if os.path.exists(FAILED_FILES_LOG):
        with open(FAILED_FILES_LOG) as file:
            error_files = file.readlines()
    # TODO: make standard testing methods
    # if os.path.exists(SUCCESS_FILES_LOG):
    #     with open(SUCCESS_FILES_LOG) as file:
    #         success_files = file.readlines()

    failed = open(FAILED_FILES_LOG, "w")
    successful = open(SUCCESS_FILES_LOG, "w")

    if not test_all:
        files_to_test = error_files
    else:
        files_to_test = set(os.listdir(test_dir_path))
        # also include option to not test successful

    for path in files_to_test:
        try:
            filepath = os.path.join(test_dir_path, path)
            logger.info("Testing %s\n", path)
            process_single_file(filepath, path)
            successful.write(path + "\n")
        except Exception:
            failed.write(path + "\n")
            logger.exception(
                "Error while processing file %s", path
            )
            continue

    failed.close()
    successful.close()


if __name__ == "__main__":
    process_single_file('test_documents/ambuja_cement.pdf', 'ambuja_cement')
    # process_batch("test_documents", test_all=True)
