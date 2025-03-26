from backend.constants import MODEL_NAME
from backend.log_config import logger
from backend.utils.get_groq_responses import get_groq_response

CONTEXT = """
You are an AI assistant designed to find if there is a speaker playing the role of moderator from a
given transcript of a meeting.

A moderator is a person who starts the meeting, introduces participants, lets other people speak
and directs the flow of conversation. He does not participate in the conversation himself.

You will be provided with some text, in which names of speakers are given along with what they said
in the form of <speaker>: <speech> format. Check if any of the speakers is a moderator and return 
that name only, in JSON format.

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
    "moderator":"Vipul Manupatra"
}"""


class CheckModerator:
    """Find moderator if exists in text and return name."""
    def process(page_text: str):
        """Takes in a text and finds if a moderator exists.
        
        Args:
            page_text (str): Extracted transcript from pdf of conference call, single page only.
        """
        logger.debug("Request received to find moderator through name.")
        messages = [
            {"role": "system", "content": CONTEXT},
            {"role": "user", "content": page_text},
        ]
        try:
            response = get_groq_response(messages=messages, model=MODEL_NAME)
        except Exception:
            logger.exception("Could not get groq response for management extraction")
        return response
