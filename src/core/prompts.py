from pprint import pprint
from dotenv import load_dotenv
import os

load_dotenv()


def getPrompts() -> dict:
    base_prompt = os.getenv("BASE_PROMPT")
    prompt_image_analysis = os.getenv("PROMPT_IMAGE_ANALYSIS")
    model = os.getenv("MODEL")

    pprint({"INFO": "Loaded prompts"})

    return {
        "model": model,
        "base_prompt": base_prompt,
        "prompt_image_analysis": prompt_image_analysis,
    }
