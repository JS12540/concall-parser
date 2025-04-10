from concall_parser.log_config import logger
from concall_parser.parser import ConcallParser


def process_single_file(filepath: str):
    """Run a single file and save its output and log."""
    logger.debug("Starting testing for %s", filepath)
    parser = ConcallParser()

    transcript_dict = parser.get_document_transcript(filepath=filepath)

    extarct_all = parser.extract_all(transcript=transcript_dict)

    print(f"Extracted all: {extarct_all}")


if __name__ == "__main__":
    process_single_file(r"test_documents\skf_india.pdf")
