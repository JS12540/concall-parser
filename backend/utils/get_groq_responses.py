from groq import Groq
from utils.get_env_vars import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


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
    except Exception as e:
        print(f"Groq API error: {e}")
        return None
