import re

from concall_parser.log_config import logger


class ManagementCaseExtractor:
    """Handles case where moderator is not present."""

    # Pre-compile the regex for performance and readability
    SPEAKER_SPEECH_PATTERN = re.compile(
        r"""
        ([A-Z]\.\s)?         # Optional initial (e.g., "J. "). Group 1.
        ([A-Za-z\s]+)        # Speaker name (e.g., "John Doe"). Group 2.
        :\s                  # Colon and space separator.
        (.*?)                # Non-greedy match for the speech content. Group 3.
        (?=                  # Positive lookahead for either:
            \s[A-Z]\.?\s?    #   Another speaker pattern (space, initial, optional dot, optional space,
            [A-Za-z\s]+:\s   #   name, colon, space).
            |                # OR
            $                #   End of the string.
        )
        """,
        re.DOTALL | re.VERBOSE,
    )

    def extract(self, transcript: dict[str, str]):
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
            matches = self.SPEAKER_SPEECH_PATTERN.findall(text)

            for initial, name, speech in matches:
                speaker = (
                    f"{(initial or '').strip()} {name.strip()}"
                ).strip()  # Clean speaker name
                speech = re.sub(r"\n", " ", speech).strip()  # Clean speech text

                if speaker not in all_speakers:
                    all_speakers.add(speaker)
                    speech_pair[speaker] = []

                speech_pair[speaker].append(speech)

        logger.debug(f"Extracted Speakers: {all_speakers}")
        return speech_pair
