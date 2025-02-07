from pprint import pprint
import openai
from openai import AuthenticationError, RateLimitError, APIConnectionError


def _make_request(messages: list, model: str = "gpt-4o", temperature: float = 1):
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

    except AuthenticationError:
        pprint("❌ Authentication error.")
        return "Authentication failed."
    except RateLimitError:
        pprint("⚠ Rate limit exceeded.")
        return "Rate limit exceeded."
    except APIConnectionError:
        pprint("🌐 API connection error.")
        return "API connection error."
    except Exception as e:
        pprint(f"Unexpected error: {e}")
        return "An unexpected error occurred."


class OpenAIChat:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.user_histories = {}
        openai.api_key = self.api_key

        self.full_system_prompt = """"""

    def get_answer_ai(self, user_id: int, user_message: str, temperature: float = 1):
        if user_id not in self.user_histories:
            self.user_histories[user_id] = []

        self.user_histories[user_id].append({"role": "user", "content": user_message})

        self.user_histories[user_id] = self.user_histories[user_id][-10:]

        messages = [
            {"role": "system", "content": self.full_system_prompt}
        ]
        messages.extend(self.user_histories[user_id])

        response_text = _make_request(messages, temperature=temperature)

        self.user_histories[user_id].append({"role": "assistant", "content": response_text})

        return response_text
