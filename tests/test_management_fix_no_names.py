import json

import pdfplumber

from concall_parser.management_fix_no_names import handle_only_management_case


def test_handle_only_management_case(filepath: str) -> None:
    """Tests the extraction function using a provided PDF file.

    Args:
        filepath: Path to the PDF file containing the transcript.
    """
    transcript: dict[int, str] = {}

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            transcript[str(page.page_number)] = page.extract_text()

    speeches = handle_only_management_case(transcript=transcript)

    with open("output/test_management_fix.json", "w") as file:
        json.dump(speeches, file, indent=4)
