from pprint import pprint
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (ConversationHandler, ContextTypes)

from src.services.telegram.constants import SURVEY_STATES, ALLOWED_SIZES, ALLOWED_STYLES, ALLOWED_CONFIRM


def normalize_input(answer: str) -> str:
    return answer.strip().lower()


async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pprint({"INFO": "start_survey -> ask for SIZE."})
    size_keyboard = [["XS", "S"], ["M", "L", "XL"]]
    reply_markup = ReplyKeyboardMarkup(size_keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "📏 Оберіть ваш розмір одягу (або введіть один з варіантів: XS, S, M, L, XL):",
        reply_markup=reply_markup
    )
    return SURVEY_STATES["SIZE"]


async def size_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer_raw = update.message.text
    pprint({"INFO": f"size_handler -> user typed: {answer_raw}"})

    answer_norm = normalize_input(answer_raw)
    allowed_lower = [s.lower() for s in ALLOWED_SIZES]

    if answer_norm not in allowed_lower:
        await update.message.reply_text(
            "Будь ласка, введіть один з варіантів: XS, S, M, L або XL."
        )
        return SURVEY_STATES["SIZE"]

    index = allowed_lower.index(answer_norm)
    chosen_size = ALLOWED_SIZES[index]
    context.user_data["size"] = chosen_size

    style_keyboard = [["Casual", "Smart Casual"], ["Classic", "Sporty"]]
    reply_markup = ReplyKeyboardMarkup(style_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "👗 Оберіть улюблений стиль (або введіть: Casual, Smart Casual, Classic, Sporty):",
        reply_markup=reply_markup
    )
    return SURVEY_STATES["STYLE"]


async def style_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer_raw = update.message.text
    pprint({"INFO": f"style_handler -> user typed: {answer_raw}"})

    answer_norm = normalize_input(answer_raw)
    allowed_lower = [s.lower() for s in ALLOWED_STYLES]

    if answer_norm not in allowed_lower:
        await update.message.reply_text(
            "Будь ласка, введіть: Casual, Smart Casual, Classic або Sporty."
        )
        return SURVEY_STATES["STYLE"]

    index = allowed_lower.index(answer_norm)
    chosen_style = ALLOWED_STYLES[index]
    context.user_data["style"] = chosen_style

    await update.message.reply_text("🎨 Які кольори ви уникаєте? (введіть будь-який текст)")
    return SURVEY_STATES["COLORS"]


async def colors_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    pprint({"INFO": f"colors_handler -> user typed: {answer}"})

    context.user_data["colors"] = answer
    await update.message.reply_text("🛍 Які бренди вам подобаються? (введіть будь-який текст)")
    return SURVEY_STATES["BRANDS"]


async def brands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    pprint({"INFO": f"brands_handler -> user typed: {answer}"})

    context.user_data["brands"] = answer
    await update.message.reply_text("📏 Який у вас зріст (см)? (введіть будь-який текст)")
    return SURVEY_STATES["HEIGHT"]


async def height_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    pprint({"INFO": f"height_handler -> user typed: {answer}"})

    context.user_data["height"] = answer
    await update.message.reply_text("⚖ Яка у вас вага (кг)? (введіть будь-який текст)")
    return SURVEY_STATES["WEIGHT"]


async def weight_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    pprint({"INFO": f"weight_handler -> user typed: {answer}"})

    context.user_data["weight"] = answer

    summary = (
        f"📋 *Ваші відповіді:*\n"
        f"• 📏 Розмір: {context.user_data['size']}\n"
        f"• 👗 Стиль: {context.user_data['style']}\n"
        f"• 🎨 Уникнені кольори: {context.user_data['colors']}\n"
        f"• 🛍 Бренди: {context.user_data['brands']}\n"
        f"• 📏 Зріст: {context.user_data['height']}\n"
        f"• ⚖ Вага: {context.user_data['weight']}\n\n"
        "Перевірте, чи все вірно.\n"
        f"Ведіть або виберіть підтверджую, скасувати"
    )

    confirm_keyboard = [["Підтверджую", "Скасувати"]]
    reply_markup = ReplyKeyboardMarkup(confirm_keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=reply_markup)
    return SURVEY_STATES["CONFIRM"]


async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer_raw = update.message.text.strip()
    pprint({"INFO": f"confirm_handler -> user typed: {answer_raw}"})

    answer_norm = normalize_input(answer_raw)
    allowed_confirms = [x.lower() for x in ALLOWED_CONFIRM]

    if answer_norm not in allowed_confirms:
        await update.message.reply_text(
            "Будь ласка, введіть 'Підтверджую' або 'Скасувати'."
        )
        return SURVEY_STATES["CONFIRM"]

    if answer_norm == "підтверджую":
        user_id = update.message.from_user.id
        user_data = context.user_data
        telegram_service = context.bot_data["telegram_service"]
        telegram_service.save_survey(user_id, user_data)

        await update.message.reply_text("✅ Дякуємо! Анкету збережено.", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("❌ Анкету скасовано. Для повтору введіть /start_survey.",
                                        reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()

    return ConversationHandler.END