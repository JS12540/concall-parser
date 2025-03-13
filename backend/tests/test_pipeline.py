import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.pipeline import ConferenceCallPipeline

pipeline = ConferenceCallPipeline()

TEST_DOCUMENT_DIR_PATH = 'backend/documents/feb_25/'
OUTPUT_DIR_PATH = 'backend/output/'

for document_path in os.listdir(path=TEST_DOCUMENT_DIR_PATH):
    dialogues = pipeline.run_pipeline(os.path.join(TEST_DOCUMENT_DIR_PATH, document_path))
    for dialogue_type, dialogue in dialogues.items():
        output_path = os.path.join(OUTPUT_DIR_PATH, f'{document_path}/{dialogue_type}.json')
        with open(output_path, 'w') as file:
            json.dump(dialogues['dialogue_type'], file, indent=4)
    break