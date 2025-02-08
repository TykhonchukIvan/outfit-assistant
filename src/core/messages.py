import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "..", "..", "localization", "messages.json")

with open(file_path, "r", encoding="utf-8") as file:
    MESSAGES = json.load(file)