from backend.constants import MODEL_NAME
from backend.log_config import logger
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

"""  # noqa: E501


SPEAKER_SELECTION_CONTEXT = """
You're given a list of strings, each of which can be a person's name or some other string 
(such as a sentence). Given this, classify each string into one of the two categories.

Extract and return the information in the following JSON format:

{
    "speaker": ["person_1", "person_2", "person_3"],
    "other": ["other_text_1","other_text_2"]
}

Note: I am interested in the person names, that is my relevant category.

Example:

{
    "speaker": ["Sonali Salgaonkar", "Guruprasad Mudlapur", "Kunal Dhamesha"],
    "other": ["Disclaimer", "Currently, 34 wells have been put on stream", "\u2013 Managing Director and Chief Executive Officer, Siemens Limited - Thank you very much and all the best and a very happy year ahead."]
}

Ensure:

The response strictly follows the JSON format.
Only include relevant management personnel and company name.
If no management information is found, return an empty dict: {}.
"""  # noqa: E501


class ExtractManagement:
    """Class to extract management information from a PDF document."""

    @staticmethod
    def process(page_text: str, speakers: list[str]) -> str | None:
        """Process the given page text to extract relevant management information.

        Args:
            page_text (str): The text content of a page from which management
                information will be extracted.
            speakers (list[str]): List of speakers extracted in Apollo case.

        Returns:
            None
        """
        logger.debug("Request to extract management details")
        if page_text != "":
            messages = [
                {"role": "system", "content": CONTEXT},
                {"role": "user", "content": page_text},
            ]
        else:
            messages = [
                {"role": "system", "content": SPEAKER_SELECTION_CONTEXT},
                {"role": "user", "content": page_text},
            ]

        # TODO: figure out how to pass that speaker list in
        try:
            response = get_groq_response(messages=messages, model=MODEL_NAME)
        except Exception:
            logger.exception("Could not get groq response for management extraction")

        return response
