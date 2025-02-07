from pprint import pprint
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_message = update.message.text.strip()
    pprint({"INFO": f"handle_message from user={user_id}", "message": user_message})

    if context.user_data.get("awaiting_phone"):
        if any(ch.isdigit() for ch in user_message):
            phone_number = user_message
            first_name = update.message.from_user.first_name or ""
            last_name = update.message.from_user.last_name or ""

            context.user_data["awaiting_phone"] = False
            reply_markup = ReplyKeyboardRemove()
            await update.message.reply_text(f"✅ Ваш номер збережено: {phone_number}", reply_markup=reply_markup)

            telegram_service = context.bot_data["telegram_service"]
            mediator = context.bot_data["service_mediator"]

            existing_user = mediator.dynamo_db.get_user(str(user_id))
            if existing_user:
                if existing_user.get("survey_completed") is True:
                    await telegram_service.send_message(user_id, "🔓 Ви вже зареєстровані та анкету заповнили!")
                else:
                    await telegram_service.send_message(user_id, "Ви вже зареєстровані, але анкету не заповнили.")
                    await telegram_service.start_survey(user_id)
            else:
                if telegram_service.registration_callback:
                    pprint({"INFO": "New user (web version phone) -> registration callback"})
                    await telegram_service.registration_callback(user_id, {
                        "phone_number": phone_number,
                        "first_name": first_name,
                        "last_name": last_name
                    })
        else:
            await update.message.reply_text("Будь ласка, введіть ваш номер телефону (наприклад, 0971234567).")
        return

    telegram_service = context.bot_data["telegram_service"]
    if telegram_service.message_callback:
        await telegram_service.message_callback(user_id, user_message)
