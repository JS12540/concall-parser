import json
import os

import pytest

from concall_parser.log_config import logger
from concall_parser.parser import ConcallParser

PDF_DIR = "tests/test_documents"


@pytest.mark.parametrize("pdf_file", [
    os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.endswith(".pdf")
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
