from backend.constants import MODEL_NAME
from backend.utils.get_groq_responses import get_groq_response

CONTEXT = """
Classify the following moderator statement into one of the three categories:
- Opening (if it's the start of the call)
- Analyst Q&A Start (if it's introducing an analyst)
- End (if it's closing the call)

Statement: Moderator statement
Response should be only one of: "Opening", "Analyst Q&A", "End".

Response should be in json format , like this:
{
    "intent": "Opening"
}
"""


class ClassifyModeratorIntent:
    """Classify moderator statements into categories."""

    @staticmethod
    def process(dialogue):
        """Classify a moderator statement into one of the three categories.

        Args:
            dialogue (str): The moderator's statement to be classified

        Returns:
            str: The classified category
        """
        messages = [
            {"role": "system", "content": CONTEXT},
            {"role": "user", "content": dialogue},
        ]

        response = get_groq_response(messages=messages, model=MODEL_NAME)

        return response
