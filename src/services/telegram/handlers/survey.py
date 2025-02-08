from pprint import pprint
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (ConversationHandler, ContextTypes)

from src.core.messages import MESSAGES
from src.services.telegram.constants import SURVEY_STATES, ALLOWED_SIZES, ALLOWED_STYLES
from src.utils.normalize_answer_bot import normalize_answer, normalize_input


async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pprint({"INFO": "start_survey -> ask for SIZE."})
    size_keyboard = [["XS", "S"], ["M", "L", "XL"]]
    reply_markup = ReplyKeyboardMarkup(size_keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(MESSAGES["select_clothing_size"], reply_markup=reply_markup)
    return SURVEY_STATES["SIZE"]


async def size_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer_raw = update.message.text
    pprint({"INFO": f"size_handler -> user typed: {answer_raw}"})

    answer_norm = normalize_input(answer_raw)
    allowed_lower = [s.lower() for s in ALLOWED_SIZES]

    if answer_norm not in allowed_lower:
        await update.message.reply_text(MESSAGES["invalid_clothing_size"])
        return SURVEY_STATES["SIZE"]

    index = allowed_lower.index(answer_norm)
    chosen_size = ALLOWED_SIZES[index]
    context.user_data["size"] = chosen_size

    style_keyboard = [["Casual", "Smart Casual"], ["Classic", "Sporty"]]
    reply_markup = ReplyKeyboardMarkup(style_keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(MESSAGES["select_fashion_style"], reply_markup=reply_markup)
    return SURVEY_STATES["STYLE"]


async def style_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer_raw = update.message.text
    pprint({"INFO": f"style_handler -> user typed: {answer_raw}"})

    answer_norm = normalize_input(answer_raw)
    allowed_lower = [s.lower() for s in ALLOWED_STYLES]

    if answer_norm not in allowed_lower:
        await update.message.reply_text(MESSAGES["invalid_fashion_style"])
        return SURVEY_STATES["STYLE"]

    index = allowed_lower.index(answer_norm)
    chosen_style = ALLOWED_STYLES[index]
    context.user_data["style"] = chosen_style

    await update.message.reply_text(MESSAGES["preferred_colors"])
    return SURVEY_STATES["COLORS"]


async def colors_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    pprint({"INFO": f"colors_handler -> user typed: {answer}"})

    context.user_data["colors"] = answer
    await update.message.reply_text(MESSAGES["favorite_brands"])
    return SURVEY_STATES["BRANDS"]


async def brands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    pprint({"INFO": f"brands_handler -> user typed: {answer}"})

    context.user_data["brands"] = answer
    await update.message.reply_text(MESSAGES["height_question"])
    return SURVEY_STATES["HEIGHT"]


async def height_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    pprint({"INFO": f"height_handler -> user typed: {answer}"})

    context.user_data["height"] = answer
    await update.message.reply_text(MESSAGES["weight_question"])
    return SURVEY_STATES["WEIGHT"]


async def weight_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer_raw = update.message.text.strip()
    answer = normalize_answer(answer_raw)
    context.user_data["weight"] = answer

    gender_keyboard = [[MESSAGES["male"], MESSAGES["female"]]]
    reply_markup = ReplyKeyboardMarkup(gender_keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(MESSAGES["select_gender"], reply_markup=reply_markup)
    return SURVEY_STATES["GENDER"]


async def gender_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer_raw = update.message.text.strip()
    answer = normalize_answer(answer_raw)
    context.user_data["gender"] = answer

    summary = (
        f"📋 *{MESSAGES['summary_title']}*\n"
        f"• 📏 {MESSAGES['size']}: {context.user_data['size']}\n"
        f"• 👗 {MESSAGES['style']}: {context.user_data['style']}\n"
        f"• 🎨 {MESSAGES['avoided_colors']}: {context.user_data['colors']}\n"
        f"• 🛍 {MESSAGES['brands']}: {context.user_data['brands']}\n"
        f"• 📏 {MESSAGES['height']}: {context.user_data['height']}\n"
        f"• ⚖ {MESSAGES['weight']}: {context.user_data['weight']}\n"
        f"• 👤 {MESSAGES['gender']}: {context.user_data['gender']}\n\n"
        f"{MESSAGES['check_correctness']}\n"
        f"{MESSAGES['enter_or_choose']} {MESSAGES['confirm']}, {MESSAGES['cancel']}"
    )

    confirm_keyboard = [[MESSAGES["confirm"], MESSAGES["cancel"]]]
    reply_markup = ReplyKeyboardMarkup(confirm_keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=reply_markup)
    return SURVEY_STATES["CONFIRM"]


async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer_raw = update.message.text.strip()
    user_id = update.message.from_user.id
    answer = normalize_answer(answer_raw)

    if answer in ["підтверджую", "confirm"]:
        user_data = context.user_data
        telegram_service = context.bot_data["telegram_service"]
        telegram_service.save_survey(user_id, user_data)

        await update.message.reply_text(
            MESSAGES["survey_saved"],
            reply_markup=ReplyKeyboardMarkup(
                [[MESSAGES["yes"], MESSAGES["no"]]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return SURVEY_STATES["ASK_UPLOAD"]
    else:
        await update.message.reply_text(MESSAGES["survey_cancelled"], reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END
