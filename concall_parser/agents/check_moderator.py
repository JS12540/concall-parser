from concall_parser.log_config import logger
from concall_parser.utils.get_groq_responses import get_groq_response

CONTEXT = """
You are an AI assistant designed to find if there is a speaker playing the role of moderator from a
given transcript of a meeting.

A moderator is a person who starts the meeting, introduces participants, lets other people speak
and directs the flow of conversation. He does not participate in the conversation himself.

You will be provided with some text, in which names of speakers are given along with what they said
in the form of <speaker>: <speech> format. Check if any of the speakers is a moderator and return
that name only, as a JSON object.

Example:
Input:
Vipul Manupatra:  Good  evening, everyone.  Welcome  to  the XYZ  (India) Limited  Q3FY25  Earnings
Conference Call. Joining us today from the management, we have Mr. Sanjay, Founder and Vice
Chairman; Mr. Hitesh, Co-Promoter and MD; and Mr. Chintan, Director and CFO.
Before we begin, we would like to draw your to the detailed disclaimer included in the presentation
for good order sake. Please note that this conference call is being recorded. All participant lines
will be in listen-only mode, and there will be an opportunity for questions and answers after the
presentation concludes. Now, I'd like to hand over the call to Mr. Hitesh for his opening remarks.
Thank you, and over to you, Hitesh.

Hitesh:  Thank you, Vipul. Good evening, everyone. Welcome to XYZ's earnings call for the third
quarter of FY25.

Output:
{
    "moderator": "Vipul Manupatra"
}

Example 2:
Input:
Sh B. Srinivasan:
Good evening and a very happy new year to all of you.
Very happy to welcome you to the third quarter of financial year 2025 business presentation
of Reliance Industries Limited.
As always, we have our Chief Financial Officer (CFO) V. Srikanth walking you through the
consolidated  numbers  first,  then  we  will  have  Kiran  Thomas  talk  about  Jio, we willhave
Anshuman Thakur talk about Jio numbers, then we will have Dinesh Taluja talk about retail
and Sanjay Roy talking about E&P performance, then Srikanth will come back and then
summarise. Before summarising, he will also talk about O2C performance.


Sh V. Srikanth:
Thank you, Srini, and Happy New Year to everyone.
We had a good operating quarter with strong performances in each of our segments.
Revenue growth, EBITDA growth at close to 8%, and PAT (Profit After Tax) growth close to
12%.

Output:
{
    "moderator": ""
}

Note:
Return an empty string for the "moderator" key if no moderator exists in the text.
"""


class CheckModerator:
    """Find moderator if exists in text and return name."""

    @staticmethod
    def process(page_text: str, groq_model: str) -> str:
        """Takes in a text and finds if a moderator exists.

        Intended to find moderator's name, then replace all occurences with "Moderator".

        Args:
            page_text (str): Extracted transcript from pdf of conference call, single page only.
            groq_model (str): Model to use for groq.

        Returns:
            Json string formatted as {"moderator":"<name>"} if moderator exists.
        """
        logger.debug("Request received to find moderator through name.")
        messages = [
            {"role": "system", "content": CONTEXT},
            {"role": "user", "content": page_text},
        ]
        try:
            response = get_groq_response(messages=messages, model=groq_model)
        except Exception:
            logger.exception(
                "Could not get groq response for management extraction"
            )
        return response
