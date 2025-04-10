from concall_parser.utils.get_groq_responses import get_groq_response

CONTEXT = """
Classify the following moderator statement into one of the three categories:
- opening (it's the start of the call)
- new_analyst_start (it's introducing an analyst from a new company)
- end (it's closing the call)

Statement: Moderator statement
Response should be only one of: "opening", new_analyst_start", "end".

You need to provide a reasoning for the classification. Why this intent was choosen and on what basis,

Response should be in json format for opening and end, like this:
{
    "intent": "opening"
    "reasoning": Provide a reasoning for the intent
}

If it's new_analyst_start, response should be in json format like this:
{
    "intent": "new_analyst_start",
    "analyst_name":"analyst_name present in the moderator statement",
    "analyst_company:""analyst_company present in the moderator statement"
    "reasoning": Provide a reasoning for the intent
}

EXAMPLES:

Moderator statement: "Ladies and gentlemen, good morning, and welcome to the SKF India Limited Q1 FY 2024-'25
Earnings Conference Call. "

Response:
{
    "intent": "opening"
    "reasoning": "From the moderator statement, it's the start of the call, as the moderator is welcoming everyone to the concall."
}


Moderator statement: "Thank you very much. We will now begin the question-and-answer session. The first question
is from the line of Mukesh Saraf at Avendus Spark. "

Response:
{
    "intent": "new_analyst_start"
    "analyst_name": "Mukesh Saraf"
    "analyst_company": "Avendus Spark"
    "reasoning": "From the moderator statement, it's introducing an analyst from a new company to start the Q&A session."
}

Moderator statement: "Shall we go for the closing, sir?"

Response:
{
    "intent": "end"
    "reasoning": "From the moderator statement, it's closing the call."
}
"""  # noqa


class ClassifyModeratorIntent:
    """Classify moderator statements into categories."""

    @staticmethod
    def process(dialogue: str, groq_model: str):
        """Classify a moderator statement into one of the three categories.

        Args:
            dialogue (str): The moderator's statement to be classified
            groq_model (str): The model to use for groq

        Returns:
            str: The classified category
        """
        messages = [
            {"role": "system", "content": CONTEXT},
            {"role": "user", "content": dialogue},
        ]

        response = get_groq_response(messages=messages, model=groq_model)

        return response
