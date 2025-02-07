from pprint import pprint
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ContextTypes


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        first_name = update.message.contact.first_name or ""
        last_name = update.message.contact.last_name or ""
        user_id = update.message.from_user.id

        reply_markup = ReplyKeyboardRemove()
        await update.message.reply_text(
            f"✅ Ваш номер збережено: {phone_number}",
            reply_markup=reply_markup
        )

        context.user_data["awaiting_phone"] = False

        telegram_service = context.bot_data["telegram_service"]
        mediator = context.bot_data["service_mediator"]

        pprint({"INFO": f"User {user_id} sent contact {phone_number}. Checking DB..."})

        existing_user = mediator.dynamo_db.get_user(str(user_id))
        if existing_user:
            if existing_user.get("survey_completed") is True:
                await telegram_service.send_message(user_id, "🔓 Ви вже зареєстровані та анкету заповнили!")
            else:
                await telegram_service.send_message(user_id, "Ви вже зареєстровані, але анкету не заповнили.")
                await telegram_service.start_survey(user_id)
        else:
            if telegram_service.registration_callback:
                pprint({"INFO": "New user -> registration callback"})
                await telegram_service.registration_callback(user_id, {
                    "phone_number": phone_number,
                    "first_name": first_name,
                    "last_name": last_name
                })


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pprint({"INFO": "/start command invoked"})
    keyboard = [[KeyboardButton("📲 Надіслати номер", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    context.user_data["awaiting_phone"] = True

    await update.message.reply_text(
        "Вітаю! Натисніть кнопку, щоб поділитися номером.\n"
        "Якщо ви у веб-версії, введіть свій номер у повідомленні.",
        reply_markup=reply_markup,
    )
