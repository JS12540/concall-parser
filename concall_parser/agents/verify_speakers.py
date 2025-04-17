from concall_parser.utils.get_groq_responses import get_groq_response

CONTEXT = """You are analyzing potential speaker names extracted from an earnings call transcript.
Task: Identify which of the following candidates are plausible speaker identifiers. 
A speaker identifier must be either a human name (first name, last name, full name, potentially with titles like Dr., Mr., Ms.) OR the specific word "Moderator" or "Operator". Ignore corporate names, section titles (like 'Now coming to Liabilities'), dates, locations, or other labels.

Instructions: Respond in the given format in JSON as given.
There will be a key output, mapped to the list containing strings of the candidates that ARE plausible speaker identifiers according to the rules.

Format:
{"output":["name_1", "name_2"]}

Example Outputs based on different 'Candidates' inputs:

Case 1:
Candidates:
- John Smith
- Acme Corp
- Moderator
- Q3 2023 Results
- Jane Doe

Output:
{"output":["John Smith", "Moderator", "Jane Doe"]}

Case 2:
Candidates:
- Thank you for joining
- Operator
- Dr. Emily Carter
- Investor Relations
- October 2024

Output:
{"output":["Operator", "Dr. Emily Carter"]}

Case 3:
Candidates:
- Now turning to questions
- Ms. Olivia Brown
- Conference Call Transcript
- Moderator

Output:
{"output":["Ms. Olivia Brown", "Moderator"]}

Case 4:
Candidates:
- Analyst Remarks
- Robert Jones
- Date
- Next Quarter Outlook
- Sarah Miller

Output:
{"output":["Robert Jones", "Sarah Miller"]}

Case 5:
Candidates:
- Company Presentation
- Financial Highlights
- Moderator

Output:
{"output":["Moderator"]}

Case 6:
Candidates:
- First Name
- Last Name
- Full Name
- Title

Output:
{"output":[]}

Remember: Your response should ONLY be the JSON list of plausible speaker identifiers extracted from the 'Candidates' list you will provide."""# noqa: E501

class VerifySpeakerNames:
    """Finds actual names from extracted speaker pattern."""

    @staticmethod
    def process(speakers: str, groq_model: str):
        """Returns the actual names out of all the speaker pattern matches provided.

        Args:
            speakers (str): Concatenated speaker pattern matches.
            groq_model (str): The model to use for groq

        Returns:
            str: The classified category
        """
        messages = [
            {"role": "system", "content": CONTEXT},
            {"role": "user", "content": speakers},
        ]

        response = get_groq_response(messages=messages, model=groq_model)

        return response
