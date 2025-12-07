import json
import pathlib

import pytest

from concall_parser.log_config import logger
from concall_parser.parser import ConcallParser

PDF_DIR = "tests/test_documents"


@pytest.mark.parametrize("pdf_file", [
    str(p) for p in pathlib.Path(PDF_DIR).glob("*.pdf")
])
def test_pdf_parser_regression(pdf_file, data_regression):
    """Test against saved working version of output."""
    data_regression.maxDiff = None
    logger.info(f"Testing for file {pdf_file}")
    parser = ConcallParser(path=pdf_file)
    try:
        result = parser.extract_all()
        logger.debug(f"extracted data: \n{json.dumps(result, indent=4)}")
        data_regression.check(result)
    except Exception as e:
        logger.error(f"Failed on file: {pdf_file} with error: {str(e)}")
        raise
