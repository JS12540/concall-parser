from backend.constants import MODEL_NAME
from backend.utils.get_groq_responses import get_groq_response

CONTEXT = """
You are an AI assistant designed to extract management information from text.
Given a document page, identify the names of management personnel and their corresponding designations.

Extract and return the information in the following JSON format:

{
   "management_name_1": "designation_1",
   "management_name_2": "designation_2",
}

Ensure:

The response strictly follows the JSON format.
Only include relevant management personnel.
If no management information is found, return an empty dict: {}.

"""  # noqa


class ExtractManagement:
    """Class to extract management information from a PDF document."""

    @staticmethod
    def process(page_text):
        """Process the given page text to extract relevant management information.

        Args:
            page_text (str): The text content of a page from which management
                            information will be extracted.

        Returns:
            None
        """
        messages = [
            {"role": "system", "content": CONTEXT},
            {"role": "user", "content": page_text},
        ]

        response = get_groq_response(messages=messages, model=MODEL_NAME)

        return response
