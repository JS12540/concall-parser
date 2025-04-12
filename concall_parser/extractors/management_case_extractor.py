import re

from concall_parser.log_config import logger


class ManagementCaseExtractor:
    """Handles case where moderator is not present."""
    def extract(self, transcript:dict[int,str]):
        """Extracts speaker names and their corresponding speeches from the transcript.
        
        To be used when moderator is not present in transcript.

        Args:
            transcript: A dictionary where keys are page numbers (as strings) and
                values are extracted text.

        Returns:
            speech_pair: A dictionary mapping speaker names to a list of their spoken segments.
        """
        all_speakers = set()
        speech_pair: dict[str, list[str]] = {}

        for _, text in transcript.items():
            matches = re.findall(
                r"([A-Z]\.\s)?([A-Za-z\s]+):\s(.*?)(?=\s[A-Z]\.?\s?[A-Za-z\s]+:\s|$)",
                text,
                re.DOTALL,
            )

            for initial, name, speech in matches:
                speaker = (
                    f"{(initial or '').strip()} {name.strip()}".strip()
                )  # Clean speaker name
                speech = re.sub(r"\n", " ", speech).strip()  # Clean speech text

                if speaker not in all_speakers:
                    all_speakers.add(speaker)
                    speech_pair[speaker] = []

                speech_pair[speaker].append(speech)

        logger.debug(f"Extracted Speakers: {all_speakers}")
        return speech_pair