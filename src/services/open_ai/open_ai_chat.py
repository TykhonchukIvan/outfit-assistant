import json

import openai
from openai import AuthenticationError, RateLimitError, APIConnectionError
from pprint import pprint

from src.core.prompts import getPrompts


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


def _parse_outfit_response(response_text: str) -> list:
    try:
        data = json.loads(response_text)
        return data.get("outfit", [])
    except json.JSONDecodeError:
        pprint({"ERROR": "Response is not valid JSON", "response": response_text})
        return []


class OpenAIChat:
    def __init__(self, api_key: str):
        self.prompts = getPrompts()
        self.api_key = api_key
        self.user_histories = {}
        openai.api_key = self.api_key

    def get_answer_ai(self, user_id: int, user_message: str, temperature: float = 1, user_info_formated: str = ""):
        if user_id not in self.user_histories:
            self.user_histories[user_id] = []

        self.user_histories[user_id].append({"role": "user", "content": user_message})

        self.user_histories[user_id] = self.user_histories[user_id][-10:]

        messages = [
            {"role": "system", "content": self.prompts["base_prompt"]},
            {"role": "user", "content": f"INFO USE IN YOUR ANSWER {user_info_formated}"}
        ]
        messages.extend(self.user_histories[user_id])

        response_text = _make_request(messages, temperature=temperature, model=self.prompts["model"])

        self.user_histories[user_id].append({"role": "assistant", "content": response_text})

        return response_text

    def vision_img(self, url: str):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.prompts["prompt_image_analysis"]},
                    {
                        "type": "image_url",
                        "image_url": {"url": url},
                    },
                ],
            }
        ]

        response_text = _make_request(messages=messages, temperature=1, model=self.prompts["model"])
        return response_text

    def find_style(self, wardrobe_list_str: str, style_description: str):
        prompt = f"""
        You are an AI personal stylist. The user has the following wardrobe items (each has a 'summary'):

        {wardrobe_list_str}

        The user wants an outfit based on this style description:
        "{style_description}"

        **Your task**:
        - Select exactly one item per category (e.g., 1 top, 1 bottom, 1 jacket, etc.) from the user’s wardrobe that best matches the style description and complements each other.
        - Ensure no duplicate categories.
        - **Return ONLY a valid JSON object, with NO extra text, NO markdown formatting, and NO explanations.**
        - The response must be in this format:
        {{
            "outfit": ["s3_key_1", "s3_key_2"]
        }}

        If you cannot find enough items to create a complete outfit, still provide the best partial combination.
        """

        messages = [
            {"role": "system", "content": "You are an AI that outputs only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        response_text = _make_request(messages=messages, model=self.prompts["model"], temperature=1)

        outfit = _parse_outfit_response(response_text)

        pprint({"INFO": "OpenAI style result", "response": response_text, "outfit": outfit})

        return outfit
