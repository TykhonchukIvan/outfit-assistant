from pprint import pprint
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ChatAction

from src.core.messages import MESSAGES
from src.services.telegram.constants import SURVEY_STATES
from src.services.telegram.handlers.contact import start, handle_contact
from src.services.telegram.handlers.message import handle_message
from src.services.telegram.handlers.survey import start_survey, size_handler, style_handler, colors_handler, \
    brands_handler, height_handler, weight_handler, confirm_handler, gender_handler
from src.services.telegram.handlers.upload import ask_upload_handler, handle_wardrobe_photo, done_photo


class TelegramService:
    def __init__(self, telegram_bot_token: str, registration_callback=None, message_callback=None,
                 save_survey_callback=None, find_user_callback=None, upload_user_photo_callback=None,
                 generate_tempo_url_callback=None, vision_wardrobe_photo_callback=None, update_wardrobe_callback=None):
        self.telegram_bot_token = telegram_bot_token
        self.registration_callback = registration_callback
        self.message_callback = message_callback
        self.save_survey_callback = save_survey_callback
        self.find_user_callback = find_user_callback
        self.upload_user_photo_callback = upload_user_photo_callback
        self.generate_tempo_url_callback = generate_tempo_url_callback
        self.vision_wardrobe_photo_callback = vision_wardrobe_photo_callback
        self.update_wardrobe_callback = update_wardrobe_callback

        self.app = ApplicationBuilder().token(self.telegram_bot_token).build()
        self.app.bot_data["telegram_service"] = self

    async def handle_send_typing(self, user_id: int):
        await self.app.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    async def send_message(self, user_id: int, message: str):
        pprint({"INFO": f"Sending message to user={user_id}"})
        await self.app.bot.send_message(chat_id=user_id, text=message)

    async def send_media_group(self, user_id, media_group):
        await self.app.bot.send_media_group(chat_id=user_id, media=media_group)

    async def start_survey(self, user_id: int):
        pprint({"INFO": f"Prompt user={user_id} to start survey."})
        await self.send_message(user_id, MESSAGES["start_survey_prompt"])

    def save_survey(self, user_id, survey_data):
        pprint({"INFO": f"save_survey called for user={user_id}"})
        if self.save_survey_callback:
            self.save_survey_callback(user_id, survey_data)

    def _register_handlers(self):
        survey_handler = ConversationHandler(
            entry_points=[CommandHandler("start_survey", start_survey)],
            states={
                SURVEY_STATES["SIZE"]: [MessageHandler(filters.TEXT & ~filters.COMMAND, size_handler)],
                SURVEY_STATES["STYLE"]: [MessageHandler(filters.TEXT & ~filters.COMMAND, style_handler)],
                SURVEY_STATES["COLORS"]: [MessageHandler(filters.TEXT & ~filters.COMMAND, colors_handler)],
                SURVEY_STATES["BRANDS"]: [MessageHandler(filters.TEXT & ~filters.COMMAND, brands_handler)],
                SURVEY_STATES["HEIGHT"]: [MessageHandler(filters.TEXT & ~filters.COMMAND, height_handler)],
                SURVEY_STATES["WEIGHT"]: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_handler)],
                SURVEY_STATES["GENDER"]: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender_handler)],
                SURVEY_STATES["CONFIRM"]: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_handler)],
                SURVEY_STATES["ASK_UPLOAD"]: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_upload_handler)],
                SURVEY_STATES["PHOTO_UPLOAD"]: [
                    MessageHandler(filters.PHOTO, handle_wardrobe_photo),
                    CommandHandler("done_photo", done_photo)
                ],
            },
            fallbacks=[]
        )
        self.app.add_handler(CommandHandler("start", start))
        self.app.add_handler(survey_handler)
        self.app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    def run(self):
        pprint({"INFO": "TelegramService run_polling() started."})
        self._register_handlers()
        self.app.run_polling()
