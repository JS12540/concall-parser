import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.pipeline import ConferenceCallPipeline

pipeline = ConferenceCallPipeline()

TEST_DOCUMENT_DIR_PATH = "test_documents/"
OUTPUT_BASE_PATH = "output/"

for document_path in os.listdir(path=TEST_DOCUMENT_DIR_PATH):
    dialogues = pipeline.run_pipeline(
        os.path.join(TEST_DOCUMENT_DIR_PATH, document_path)
    )
    for dialogue_type, dialogue in dialogues.items():
        output_dir_path = os.path.join(
            OUTPUT_BASE_PATH, f"{os.path.basename(document_path)}"
        )
        os.makedirs(output_dir_path, exist_ok=True)
        with open(os.path.join(output_dir_path, f"{dialogue_type}.json"), "w") as file:
            json.dump(dialogue, file, indent=4)
    break
