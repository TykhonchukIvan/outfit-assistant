import base64
import os
from pprint import pprint
import re
import io
from telegram import InputMediaPhoto

from src.core.config import getConfig
from src.core.messages import MESSAGES
from src.services.bucket_s3.bucket_s3_service import S3ImageStorage
from src.services.dynamo_db.dynamo_db_service import DynamoDBService
from src.services.open_ai.open_ai_chat import OpenAIChat
from src.services.telegram.telegram_service import TelegramService


class ServiceMediator:
    def __init__(self):
        config = getConfig()

        self.telegram_service = TelegramService(
            message_callback=self.process_message,
            telegram_bot_token=config["telegram_bot_token"],
            find_user_callback=self.find_user,
            save_survey_callback=self.save_survey_data,
            registration_callback=self.handle_registration,
            update_wardrobe_callback=self.update_wardrobe,
            upload_user_photo_callback=self.upload_user_photo,
            generate_tempo_url_callback=self.generate_tempo_url,
            vision_wardrobe_photo_callback=self.vision_wardrobe_photo
        )
        self.openai_chat = OpenAIChat(api_key=config["open_ai_api_key"])
        self.dynamo_db = DynamoDBService(
            region_name=config["region_name"],
            dynamo_table_name=config["dynamo_table_name"],
        )
        self.s3_storage = S3ImageStorage(
            bucket_name=config["s3_name"],
            region_name=config["region_name"],
        )

        pprint({"INFO": "ServiceMediator initialized."})

    async def handle_registration(self, user_id: int, user_data: dict):
        pprint({"INFO": f"handle_registration -> user_id={user_id}, data={user_data}"})

        saved_user = self.dynamo_db.save_user(
            user_id,
            user_data["phone_number"],
            user_data.get("first_name", ""),
            user_data.get("last_name", "")
        )
        if saved_user:
            await self.telegram_service.send_message(user_id, MESSAGES["registration_success"])
            await self.telegram_service.start_survey(user_id)
        else:
            await self.telegram_service.send_message(user_id, MESSAGES["registration_error"])

    async def process_message(self, user_id: int, user_message: str):
        await self.telegram_service.handle_send_typing(user_id)
        user_info = self.find_user(user_id)

        user_info_formated = f"""
        last_name:{user_info["last_name"]}\n
        first_name:{user_info["first_name"]}\n
        brands:{user_info["brands"]}\n
        weight:{user_info["weight"]}\n
        style:{user_info["style"]}\n
        gender:{user_info["gender"]}\n
        colors:{user_info["colors"]}\n
        height:{user_info["height"]}\n"""

        answer = self.openai_chat.get_answer_ai(user_id, user_message, user_info_formated=user_info_formated)

        if re.search(r"<style_request>", answer):
            metadata_match = re.search(r"<metadata>(.*?)</metadata>", answer)
            style_description = metadata_match.group(1) if metadata_match else "base style"

            clean_answer = re.sub(r"<style_request>|<metadata>.*?</metadata>", "", answer).strip()
            await self.find_style(user_id, style_description)
            await self.telegram_service.send_message(user_id, clean_answer)
        else:
            await self.telegram_service.send_message(user_id, answer)

    async def find_style(self, user_id: int, style_description: str):
        user = self.dynamo_db.get_user(user_id)

        wardrobe = user.get("wardrobe", [])
        if not wardrobe:
            pprint({"INFO": f"User {user_id} has empty wardrobe."})
            return []

        wardrobe_list_str = ""
        for idx, item in enumerate(wardrobe, start=1):
            s3_key = item["s3_key"]
            summary = item["summary"].replace("\n", " ")
            wardrobe_list_str += f"{idx}) s3_key: {s3_key}\n   summary: {summary}\n\n"

        outfits = self.openai_chat.find_style(wardrobe_list_str=wardrobe_list_str, style_description=style_description)
        if len(outfits) > 0:
            await self.telegram_service.send_message(user_id, MESSAGES["wardrobe_analysis_start"])
        await self.send_style_photo(user_id=user_id, outfits=outfits)

    async def send_style_photo(self, user_id: int, outfits: list):
        media_group = []
        pprint(f"outfits, {outfits}")
        for s3_key in outfits:
            encoded_file = self.s3_storage.get_file_from_s3(s3_key)

            if encoded_file:
                file_bytes = base64.b64decode(encoded_file)
                file_name = os.path.basename(s3_key)

                file_stream = io.BytesIO(file_bytes)
                file_stream.name = file_name

                media_group.append(InputMediaPhoto(media=file_stream, caption=file_name))

        if media_group:
            pprint(f"media_group ${media_group}")
            await self.telegram_service.send_media_group(user_id=user_id, media_group=media_group)
        else:
            await self.telegram_service.send_message(user_id, MESSAGES["error_photo"])

    def find_user(self, user_id: int):
        return self.dynamo_db.get_user(user_id)

    def save_survey_data(self, user_id: int, survey_data: dict):
        pprint({"INFO": f"save_survey_data -> user_id={user_id}"})
        self.dynamo_db.update_survey(user_id, survey_data)
        pprint({"INFO": f"Survey saved for user {user_id}."})

    def upload_user_photo(self, user_id: int, image_bytes: bytes):
        return self.s3_storage.upload_user_photo(
            user_id=user_id,
            image_bytes=image_bytes,
        )

    def generate_tempo_url(self, s3_key: str):
        return self.s3_storage.generate_tempo_url_url(s3_key=s3_key)

    def vision_wardrobe_photo(self, url: str):
        return self.openai_chat.vision_img(url=url)

    def update_wardrobe(self, user_id: int, s3_key: str, summary: str):
        self.dynamo_db.update_wardrobe(user_id=user_id, s3_key=s3_key, summary=summary)

    def run(self):
        pprint({"INFO": "ServiceMediator run -> starting TelegramService."})
        self.telegram_service.run()
