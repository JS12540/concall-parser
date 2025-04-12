from concall_parser.log_config import logger
from concall_parser.parser import ConcallParser


def process_single_file(path: str):
    """Run a single file and save its output and log."""
    logger.debug("Starting testing for %s", path)
    parser = ConcallParser(path=path)

    extracted = parser.extract_commentary()
    print(f"Extracted: {extracted}")


if __name__ == "__main__":
    process_single_file(r"test_documents\Adani_total_gas.pdf")
