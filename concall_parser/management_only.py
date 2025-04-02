import re

FILEPATH = "test_documents/apollo_hospitals.pdf"


# TODO: fix unicode characters in speech
# TODO: last 2 extracted incorrectly - lines of\nbusinesses, Disclaimer

def handle_only_management_case(transcript: dict[str, str]) -> dict[str, list[str]]:
    """Extracts speaker names and their corresponding speeches from the transcript.

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
            speaker = f"{(initial or '').strip()} {name.strip()}".strip()  # Clean speaker name
            speech = re.sub(r'\n', " ", speech).strip()  # Clean speech text

            if speaker not in all_speakers:
                all_speakers.add(speaker)
                speech_pair[speaker] = []

            speech_pair[speaker].append(speech)

    print(f"Extracted Speakers: {all_speakers}")
    return speech_pair