from concall_parser.log_config import logger
from concall_parser.parser import ConcallParser


def process_single_file(path: str):
    """Run a single file and save its output and log."""
    logger.debug("Starting testing for %s", path)
    parser = ConcallParser(link=path)
    extracted = parser.extract_management_team()
    print(f"Extracted all: {extracted}")


if __name__ == "__main__":
    process_single_file(
        r"https://www.bseindia.com/xml-data/corpfiling/AttachHis/458af4e6-8be5-4ce2-b4f1-119e53cd4c5a.pdf"
    )
