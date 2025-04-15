import json

import pytest

from concall_parser.log_config import logger
from concall_parser.parser import ConcallParser

TEST_FILES = [
    "tests/test_documents/apollo_hospitals.pdf",
]

@pytest.mark.parametrize('path', TEST_FILES)
def test_single_file(path: str):
    """Run a single file and save its output and log."""
    logger.debug("Starting testing for %s", path)
    parser = ConcallParser(path=path)
    extracted = parser.extract_all()
    logger.info(f"Extracted info: {json.dumps(extracted, indent=4)}")

    assert isinstance(extracted, dict)
    assert isinstance(extracted['management'], dict)
    assert isinstance(extracted['commentary'], list)
    assert isinstance(extracted['analyst'], dict)
    assert extracted['commentary'] != []
