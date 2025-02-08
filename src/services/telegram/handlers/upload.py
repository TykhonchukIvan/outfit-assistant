import io
import base64
from pprint import pprint

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (ConversationHandler, ContextTypes)
from src.core.messages import MESSAGES
from src.utils.normalize_answer_bot import normalize_answer
from src.services.telegram.constants import SURVEY_STATES


async def ask_upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer_raw = update.message.text.strip()
    answer = normalize_answer(answer_raw)

    if answer in ["так", "yes"]:
        await update.message.reply_text(MESSAGES["send_wardrobe_photos"], reply_markup=ReplyKeyboardRemove())
        return SURVEY_STATES["PHOTO_UPLOAD"]
    else:
        await update.message.reply_text(MESSAGES["wardrobe_photo_received"], reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


async def handle_wardrobe_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_service = context.bot_data["telegram_service"]

    photo = update.message.photo[-1]
    user_id = update.message.from_user.id
    pprint({"INFO": f"handle_wardrobe_photo -> user_id={user_id}"})

    telegram_file = await context.bot.get_file(photo.file_id)

    file_bytes = io.BytesIO()
    await telegram_file.download_to_memory(out=file_bytes)

    image_content = file_bytes.getvalue()

    base64_image = base64.b64encode(image_content).decode("utf-8")
    base64_string = f"data:image/jpeg;base64,{base64_image}"

    try:
        result = telegram_service.upload_user_photo_callback(
            user_id=user_id,
            image_bytes=image_content,
        )

        await update.message.reply_text(MESSAGES["photo_processing"])

        summary = telegram_service.vision_wardrobe_photo_callback(base64_string)

        telegram_service.update_wardrobe_callback(
            user_id=user_id,
            s3_key=result["s3_key"],
            summary=summary
        )
        await update.message.reply_text(MESSAGES["photo_saved_no_url"])

    except Exception as e:
        pprint(f"{e}")
        await update.message.reply_text(MESSAGES["error_photo_upload"])

    return SURVEY_STATES["PHOTO_UPLOAD"]


async def done_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MESSAGES["wardrobe_uploaded"], reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
