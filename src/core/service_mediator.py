from pprint import pprint
from src.core.config import getConfig
from src.services.dynamo_db.dynamo_db_service import DynamoDBService
from src.services.open_ai.open_ai_chat import OpenAIChat
from src.services.telegram.telegram_service import TelegramService


class ServiceMediator:
    def __init__(self):
        config = getConfig()
        telegram_bot_token = config["telegram_bot_token"]
        openai_api_key = config["open_ai_api_key"]
        aws_access_key_id = config["aws_access_key_id"]
        aws_secret_access_key = config["aws_secret_access_key"]
        dynamo_table_name = config["dynamo_table_name"]
        region_name = config["region_name"]

        self.telegram_service = TelegramService(
            telegram_bot_token=telegram_bot_token,
            registration_callback=self.handle_registration,
            message_callback=self.process_message,
            save_survey_callback=self.save_survey_data
        )

        self.openai_chat = OpenAIChat(api_key=openai_api_key)
        self.dynamo_db = DynamoDBService(
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            dynamo_table_name=dynamo_table_name
        )

        self.telegram_service.app.bot_data["service_mediator"] = self
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
            await self.telegram_service.send_message(
                user_id,
                "🎉 Дякуємо за реєстрацію! Зараз заповнімо анкету."
            )
            await self.telegram_service.start_survey(user_id)
        else:
            await self.telegram_service.send_message(user_id, "Виникла помилка при реєстрації, спробуйте ще раз.")

    async def process_message(self, user_id: int, user_message: str):
        pprint({"INFO": f"process_message from user={user_id}", "msg": user_message})
        answer = self.openai_chat.get_answer_ai(user_id, user_message)
        pprint({"INFO": "OpenAI answer", "answer": answer})
        await self.telegram_service.send_message(user_id, answer)

    def save_survey_data(self, user_id: int, survey_data: dict):
        pprint({"INFO": f"save_survey_data -> user_id={user_id}"})
        self.dynamo_db.update_survey(user_id, survey_data)
        pprint({"INFO": f"Survey saved for user {user_id}."})

    def run(self):
        pprint({"INFO": "ServiceMediator run -> starting TelegramService."})
        self.telegram_service.run()
