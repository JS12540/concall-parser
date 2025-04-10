from concall_parser.log_config import logger
from concall_parser.utils.get_groq_responses import get_groq_response

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
(such as a sentence). Given this, return only the strings that are names, in the format given below.

Extract and return the information in the following JSON format:

{
    "person_1_name":"",
    "person_2_name":"",
    "person_3_name":"",
}

Note: I am interested in the person names, that is my relevant category.
Keep the values of the json empty, just need the keys.

Example:
Input:

"Apollo Hospitals Enterprise Limited
Transcript of Q3 FY25 Earnings Conference Call
February 11, 2025
When  we  look at the whole area  of industrial as  well.  So,  the total decorative  plus
industrial business overall combined, the performance gets slightly better given the
fact  that  industrial  segment  has  done  slightly  better  as  compared  to  the  retail
segment. When we  look at the volume growth, we are  at about 1.7%  in terms of the
overall volume growth.
Sonali Salgaonkar
Guruprasad Mudlapur
Kunal Dhamesha
Disclaimer
Currently, 34 wells have been put on stream
\u2013 Managing Director and Chief Executive Officer, Siemens Limited - Thank you very much and all the best and a very happy year ahead.


Output:
{
    "company_name": "Apollo Hospitals",
    "Sonali Salgaonkar":"",
    "Guruprasad Mudlapur":"",
    "Kunal Dhamesha":""
}

Ensure:

The response strictly follows the JSON format.
Only include relevant management personnel and company name.
If no management information is found, return an empty dict: {}.
"""  # noqa: E501


class ExtractManagement:
    """Class to extract management information from a PDF document."""

    @staticmethod
    def process(page_text: str, groq_model: str) -> str:
        """Process the given page text to extract relevant management information.

        Args:
            page_text (str): The text content of a page from which management
                information will be extracted.
            groq_model (str): The model to use for Groq queries.

        Returns:
            None
        """
        # TODO: context selection logic is wrong, recheck
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

        # TODO: update data model of response in case of speaker selection
        # TODO: add company name fix in case of speaker selection
        try:
            response = get_groq_response(messages=messages, model=groq_model)
            return response
        except Exception:
            logger.exception(
                "Could not get groq response for management extraction"
            )
