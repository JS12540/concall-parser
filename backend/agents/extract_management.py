from backend.constants import MODEL_NAME
from backend.utils.get_groq_responses import get_groq_response

# TODO: add second prompt case, for apollo (may be solved using regex but idk)

CONTEXT = """
You are an AI assistant designed to extract management information and company name from text.
Given page text, identify the names of management personnel and their corresponding designations.

Extract and return the information in the following JSON format:

{
   "company_name": "company_name", // company name will come as value
   "management_name_1": "designation_1", // management name will come as key and designation will come as value
   "management_name_2": "designation_2", // management name will come as key and designation will come as value
}

Example:

{
  'company_name': 'Adani Total Gas Limited',
  'Suresh Manglani': 'Executive Director and Chief Executive Officer',
  'Parag Parikh': 'Chief Financial Officer',
  'Rahul Bhatia': 'Gas Sourcing and Business Development Head'
}

Ensure:

The response strictly follows the JSON format.
Only include relevant management personnel and company name.
If no management information is found, return an empty dict: {}.

"""  # noqa


class ExtractManagement:
    """Class to extract management information from a PDF document."""

    @staticmethod
    def process(page_text: str) -> str | None:
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
