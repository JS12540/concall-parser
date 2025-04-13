import json
import os

import pdfplumber
import requests

from concall_parser.log_config import logger


def get_document_transcript(filepath: str) -> dict[int, str]:
    """Extracts text of a pdf document.

    Args:
        filepath: Path to the pdf file whose text needs to be extracted.

    Returns:
        transcript: Dictionary of page number, page text pair.
    """
    transcript = {}
    try:
        with pdfplumber.open(filepath) as pdf:
            logger.debug("Loaded document")
            page_number = 1
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    transcript[page_number] = text
                    page_number += 1
        return transcript
    except FileNotFoundError:
        raise FileNotFoundError("Please check if file exists.")
    except Exception:
        logger.exception("Could not load file %s", filepath)


def save_output(
    dialogues: dict, document_name: str, output_base_path: str = "output"
) -> None:
    """Save dialogues to JSON files in the specified output path.

    Takes the dialogues dict as input, splits it into three parts, each saved
    as a json file in a common directory with path output_base_path/document_name.

    Args:
        dialogues (dict): Extracted dialogues, speaker-transcript pairs.
        output_base_path (str): Path to directory in which outputs are to be saved.
        document_name (str): Name of the file being parsed, corresponds to company name for now.
    """
    for dialogue_type, dialogue in dialogues.items():
        output_dir_path = os.path.join(
            output_base_path, os.path.basename(document_name)[:-4]
        )
        os.makedirs(output_dir_path, exist_ok=True)
        with open(
            os.path.join(output_dir_path, f"{dialogue_type}.json"), "w"
        ) as file:
            json.dump(dialogue, file, indent=4)


def save_transcript(
    transcript: dict,
    document_path: str,
    output_base_path: str = "raw_transcript",
) -> None:
    """Save the extracted text to a file.

    Takes in a transcript, saves it to a text file in a directory for human verification.

    Args:
        transcript (dict): Page number, page text pair extracted using pdfplumber.
        document_path (str): Path of file being processed, corresponds to company name.
        output_base_path (str): Path of directory where transcripts are to be saved.
    """
    try:
        document_name = os.path.basename(document_path)[:-4]  # remove the .pdf
        output_dir_path = os.path.join(output_base_path, document_name)
        os.makedirs(output_base_path, exist_ok=True)
        with open(f"{output_dir_path}.txt", "w") as file:
            for _, text in transcript.items():
                file.write(text)
                file.write("\n\n")
        logger.info("Saved transcript text to file\n")
    except Exception:
        logger.exception("Could not save document transcript")


def get_transcript_from_link(link:str) -> dict[int, str]:
    """Extracts transcript by downloading pdf from a given link.
    
    Args:
        link: Link to the pdf document of earnings call report.
        
    Returns:
        transcript: A page number-page text mapping.
    
    Raises:
        Http error, if encountered during downloading document.
    """
    try:
        logger.debug("Request to get transcript from link.")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"# noqa: E501
        }
        response = requests.get(url=link, headers=headers, timeout=30, stream=True)
        response.raise_for_status()

        temp_doc_path = "temp_document.pdf"
        with open(temp_doc_path, 'wb') as temp_pdf:
            for chunk in response.iter_content(chunk_size=8192):
                temp_pdf.write(chunk)
        transcript = get_document_transcript(filepath=temp_doc_path)
        os.remove(temp_doc_path)

        return transcript
    except Exception:
        logger.exception("Could not get transcript from link")
        return dict()