import re


def normalize_answer(answer: str) -> str:
    answer = answer.strip().lower()
    answer = re.sub(r"[^\w\s]", "", answer)
    return answer.strip()


def normalize_input(answer: str) -> str:
    return answer.strip().lower()