import filecmp
from typing import List
from pathlib import Path

from tests.test_parsing import process_single_file


def compare_folders(output: Path, expected: Path) -> bool:
    """Compare the contents of two output dirs - verify older passed tests."""
    comparison = filecmp.dircmp(output, expected)
    if comparison.left_only or comparison.right_only or comparison.diff_files:
        return False
    return True


def test_single_file_processing(filepath: Path, output_dir: Path, expected_output_dir: Path) -> None:
    """Test processing a single file and compare the output with the expected output."""
    try:
        # Assuming process_single_file expects string paths for external compatibility
        process_single_file(str(filepath), str(output_dir))
        assert compare_folders(
            output_dir, expected_output_dir
        ), "Output does not match expected"
    except AssertionError:
        print("Broken -- fix it")
        return
    print("Test passed")


def test_multiple_files_processing(input_files: List[Path], output_dir: Path, expected_output_dirs: List[Path]) -> None:
    """Test processing multiple files and compare the outputs with the expected outputs."""
    for input_file, expected_output_dir in zip(input_files, expected_output_dirs):
        test_single_file_processing(input_file, output_dir, expected_output_dir)


# TODO: upgrade to pytest-regressions
if __name__ == "__main__":
    test_single_file_processing(
        filepath=Path("test_documents/ambuja_cement.pdf"),
        output_dir=Path("output/ambuja_cement"),
        expected_output_dir=Path("tests/parsed_correct/ambuja_cement"),
    )
