import asyncio
import json
import os
import tempfile

import aiofiles
import httpx
import pdfplumber

from concall_parser.log_config import logger


# TODO: use aiofiles for file operations
# TODO: check out async pdf readers, if not available, use threadpool
async def get_document_transcript(filepath: str) -> dict[int, str]:
    """Extracts text of a pdf document.

    Args:
        filepath: Path to the pdf file whose text needs to be extracted.

    Returns:
        transcript: Dictionary of page number, page text pair.
    """

    def _extract_pdf_text(filepath: str) -> dict[int, str]:
        transcript = {}
        try:
            with pdfplumber.open(filepath) as pdf:
                logger.debug(f"Loaded document {filepath}")
                # ? Do we need to start a counter? can we not do pdfplumber pages or enumerate?
                page_number = 1
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        transcript[page_number] = text
                        page_number += 1
            return transcript
        except FileNotFoundError:
            logger.exception(
                f"Could not file with path {filepath}. Please check if it exists."
            )
            raise FileNotFoundError("Please check if file exists.")
        except Exception:
            logger.exception("Could not load file %s", filepath)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_pdf_text, filepath)


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
    try:
        output_dir_path = os.path.join(
            output_base_path, os.path.basename(document_name)[:-4]
        )
        os.makedirs(output_dir_path, exist_ok=True)
        for dialogue_type, dialogue in dialogues.items():
            output_file_path = os.path.join(output_dir_path, f"{dialogue_type}.json")
            async with aiofiles.open(output_file_path, "w") as file:
                await file.write(json.dump(dialogue, indent=4))
    except Exception:
        logger.exception(f"Failed to save outputs for file {output_base_path}.")


async def save_transcript(
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
        # ? concatenate all transcript texts before writing at once? IO overhead?
        async with aiofiles.open(f"{output_dir_path}.txt", "w") as file:
            for _, text in transcript.items():
                await file.write(text)
                await file.write("\n\n")
            # ? Do we gather all tasks before asynchronously executing?
        logger.info("Saved transcript text to file\n")
    except Exception:
        logger.exception("Could not save document transcript")


async def get_transcript_from_link(link: str) -> dict[int, str]:
    """Extracts transcript by downloading pdf from a given link.

    Args:
        link: Link to the pdf document of earnings call report.

    Returns:
        transcript: A page number-page text mapping.

    Raises:
        Http error, if encountered during downloading document.
    """
    try:
        # TODO: expand error handling - file operations
        logger.debug("Request to get transcript from link.")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"  # noqa: E501
        }
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as file:
            temp_file_path = file.name
        
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(url=link, timeout=30)
            response.raise_for_status()

            with aiofiles.open(temp_file_path, "wb") as file:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    await file.write(chunk)

        transcript = await get_document_transcript(filepath=temp_file_path)
        return transcript
    
    except Exception:
        logger.exception("Could not get transcript from link")
        return dict()
    
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
