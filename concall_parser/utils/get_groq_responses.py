from groq import APIStatusError, Groq

from concall_parser.log_config import logger
from concall_parser.utils.env_load import groq_api_key

client = Groq(api_key=groq_api_key)


def get_groq_response(messages, model):
    """Get response from Groq API."""
    try:
        response = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=1024,
            top_p=1,
            stop=None,
            stream=False,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content
    except APIStatusError:
        logger.exception("Groq error - check prompt size")
    except Exception:
        logger.exception("Groq response error")
    return None
