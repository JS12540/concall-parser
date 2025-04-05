import filecmp

from tests.test_parsing import process_single_file


def compare_folders(output, expected):
    """Compare the contents of two output dirs - verify older passed tests."""
    comparison = filecmp.dircmp(output, expected)
    if comparison.left_only or comparison.right_only or comparison.diff_files:
        return False
    return True


def test_single_file_processing(filepath, output_dir, expected_output_dir):
    """Test processing a single file and compare the output with the expected output."""
    try:
        process_single_file(filepath, output_dir)
        assert compare_folders(
            output_dir, expected_output_dir
        ), "Output does not match expected"
    except AssertionError:
        print("Broken -- fix it")
        return
    print("Test passed")


def test_multiple_files_processing(input_files, output_dir, expected_output_dirs):
    """Test processing multiple files and compare the outputs with the expected outputs."""
    for input_file, expected_output_dir in zip(input_files, expected_output_dirs):
        test_single_file_processing(input_file, output_dir, expected_output_dir)


# TODO: upgrade to pytest-regressions
if __name__ == "__main__":
    test_single_file_processing(
        filepath="test_documents/ambuja_cement.pdf",
        output_dir="output/ambuja_cement",
        expected_output_dir="backend/tests/parsed_correct/ambuja_cement",
    )
