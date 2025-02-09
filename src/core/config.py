from pprint import pprint
import os


def getConfig() -> dict:
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    open_ai_api_key = os.getenv("OPEN_AI_API_KEY")
    dynamo_table_name = os.getenv("DYNAMO_TABLE_NAME")
    region_name = os.getenv("REGION_NAME")
    s3_name = os.getenv("S3_NAME")

    pprint({"INFO": "Loaded config"})

    return {
        "telegram_bot_token": telegram_bot_token,
        "open_ai_api_key": open_ai_api_key,
        "dynamo_table_name": dynamo_table_name,
        "region_name": region_name,
        "s3_name": s3_name,
    }
