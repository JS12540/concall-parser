import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_GROQ_MODEL = "llama3-70b-8192"


def get_groq_api_key() -> str:
    """Get the Groq API key from the environment variable GROQ_API_KEY.

    Raises an OSError if the key is not set.

    Returns:
        str: The Groq API key.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise OSError(
            "❌ GROQ_API_KEY is not set. Please set it in your environment.\n"
            "Example (Linux/macOS): export GROQ_API_KEY=your_groq_api_key_here\n"
            "Example (Windows CMD): set GROQ_API_KEY=your_groq_api_key_here"
        )
    return api_key


def get_groq_model() -> str:
    """Get the Groq model name from the environment variable GROQ_MODEL.

    If GROQ_MODEL is not set, print a warning and return the default model name.

    Returns:
        str: The Groq model name.
    """
    model = os.getenv("GROQ_MODEL")
    if not model:
        print(f"⚠️  GROQ_MODEL not set. Using default: {DEFAULT_GROQ_MODEL}")
        return DEFAULT_GROQ_MODEL
    return model
