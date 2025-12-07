import json
import tempfile
from pathlib import Path

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
            logger.debug("Loaded document: %s", filepath)
            page_number = 1
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    transcript[page_number] = text
                    page_number += 1
        return transcript
    except FileNotFoundError:
        logger.error("File not found: %s", filepath)
        raise FileNotFoundError(f"Please check if file exists: {filepath}")
    except (pdfplumber.PDFSyntaxError, pdfplumber.PDFDataError) as e:
        logger.exception("Error parsing PDF file %s: %s", filepath, e)
        raise ValueError(f"Error parsing PDF file: {filepath}") from e
    except Exception as e:
        logger.exception("Could not load file %s: %s", filepath, e)
        raise # Re-raise the exception after logging


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
    # Use pathlib for robust path handling
    output_base_path_obj = Path(output_base_path)
    document_stem = Path(document_name).stem # Get filename without extension

    output_dir_path_obj = output_base_path_obj / document_stem
    output_dir_path_obj.mkdir(parents=True, exist_ok=True)

    for dialogue_type, dialogue in dialogues.items():
        output_file_path = output_dir_path_obj / f"{dialogue_type}.json"
        try:
            with open(output_file_path, "w", encoding="utf-8") as file:
                json.dump(dialogue, file, indent=4)
            logger.debug("Saved %s to %s", dialogue_type, output_file_path)
        except OSError as e:
            logger.exception("Could not save dialogue type %s to %s: %s", dialogue_type, output_file_path, e)
            raise # Re-raise after logging


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
        output_base_path_obj = Path(output_base_path)
        output_base_path_obj.mkdir(parents=True, exist_ok=True)

        document_name_stem = Path(document_path).stem  # Get filename without extension
        output_file_path = output_base_path_obj / f"{document_name_stem}.txt"

        with open(output_file_path, "w", encoding="utf-8") as file:
            for _, text in transcript.items():
                file.write(text)
                file.write("\n\n")
        logger.info("Saved transcript text to file: %s", output_file_path)
    except OSError as e:
        logger.exception("Could not save document transcript to %s: %s", output_file_path, e)
        raise # Re-raise after logging
    except Exception as e: # Catch any other unexpected errors
        logger.exception("An unexpected error occurred while saving transcript: %s", e)
        raise


def get_transcript_from_link(link:str) -> dict[int, str]:
    """Extracts transcript by downloading pdf from a given link.
    
    Args:
        link: Link to the pdf document of earnings call report.
        
    Returns:
        transcript: A page number-page text mapping.
    
    Raises:
        Http error, if encountered during downloading document.
    """
    transcript = dict()
    temp_doc_path = None # Initialize to None for finally block
    try:
        logger.debug("Request to get transcript from link: %s", link)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        # Use a higher timeout for potentially large PDF downloads
        response = requests.get(url=link, headers=headers, timeout=60, stream=True)
        response.raise_for_status()

        # Use tempfile for secure and automatic cleanup of temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_doc_path = Path(temp_pdf.name)
            for chunk in response.iter_content(chunk_size=8192):
                temp_pdf.write(chunk)
            logger.debug("Downloaded PDF to temporary file: %s", temp_doc_path)

        transcript = get_document_transcript(filepath=str(temp_doc_path))
        return transcript
    except requests.exceptions.RequestException as e:
        logger.exception("HTTP/Network error while getting transcript from link %s: %s", link, e)
        # Optionally re-raise a more specific custom exception if needed by calling code
        raise ConnectionError(f"Failed to download PDF from {link}") from e
    except (OSError, ValueError) as e: # Catch errors from file operations or PDF parsing
        logger.exception("File/PDF processing error after downloading from link %s: %s", link, e)
        raise
    except Exception as e:
        logger.exception("An unexpected error occurred while getting transcript from link %s: %s", link, e)
        raise
    finally:
        # Ensure the temporary file is cleaned up, even if errors occur
        if temp_doc_path and temp_doc_path.exists(): # Check if path was assigned and exists
            try:
                temp_doc_path.unlink()
                logger.debug("Cleaned up temporary file: %s", temp_doc_path)
            except OSError as e:
                logger.warning("Could not remove temporary file %s: %s", temp_doc_path, e)
