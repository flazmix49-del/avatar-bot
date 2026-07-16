from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler, ConversationHandler
from config import BOT_TOKEN, PREMIUM_PRICE, FREE_ATTEMPTS
from ai_generator import generate_avatar, generate_text, get_weather, get_advice, get_quote, get_idea, get_compatibility, get_holidays, convert_currency, get_horoscope, get_recipe, get_support_answer, get_help_menu, get_feedback_menu, save_feedback
from database import init_db, get_user, add_user, update_user_count, set_premium, reset_daily, check_premium, save_order, get_premium_days_left
import os
import random
import time
import logging
import threading
from datetime import datetime, timedelta
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ========== АВТОСБРОС ==========
def reset_all_users():
    try:
        import sqlite3
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('UPDATE users SET avatar_count = 0')
        conn.commit()
        conn.close()
        print(f"🔄 Сброс выполнен")
    except:
        pass

def schedule_reset():
    while True:
        time.sleep(43200)
        reset_all_users()

threading.Thread(target=schedule_reset, daemon=True).start()
# ===================================

WAITING_PROMPT = 1
WAITING_TEXT_PROMPT = 4
WAITING_CITY = 5
WAITING_CURRENCY = 6
WAITING_HOROSCOPE = 7
WAITING_RECIPE = 8
WAITING_FEEDBACK = 9

def main_menu(user_id):
    user_data = get_user(user_id)
    if not user_data:
        is_premium = False
        remaining = FREE_ATTEMPTS
        days_left = 0
    else:
        avatar_count, premium, premium_until = user_data
        is_premium = premium == 1 and premium_until > int(time.time())
        if is_premium:
            days_left = max(0, (premium_until - int(time.time())) // 86400)
            remaining = "∞"
        else:
            days_left = 0
            remaining = max(0, FREE_ATTEMPTS - avatar_count)
    
    keyboard = [
        [InlineKeyboardButton("🎨 Аватарка", callback_data="create"), InlineKeyboardButton("📝 Текст", callback_data="text_gen")],
        [InlineKeyboardButton("🌤 Погода", callback_data="weather"), InlineKeyboardButton("💡 Идея дня", callback_data="idea")],
        [InlineKeyboardButton("🌟 Цитата", callback_data="quote"), InlineKeyboardButton("💬 Совет", callback_data="advice")],
        [InlineKeyboardButton("💞 Совместимость", callback_data="compat"), InlineKeyboardButton("📅 Праздники", callback_data="holidays")],
        [InlineKeyboardButton("💱 Конвертер", callback_data="currency"), InlineKeyboardButton("🌟 Гороскоп", callback_data="horoscope")],
        [InlineKeyboardButton("🍳 Рецепты", callback_data="recipe"), InlineKeyboardButton("💎 Премиум", callback_data="premium_menu")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats"), InlineKeyboardButton("❓ Помощь", callback_data="help")],
        [InlineKeyboardButton("📩 Обратная связь", callback_data="feedback"), InlineKeyboardButton("🔄 Перезапустить", callback_data="main_menu")]
    ]
    
    if is_premium:
        keyboard.append([InlineKeyboardButton(f"🔥 Премиум: {days_left} дней", callback_data="noop")])
    else:
        keyboard.append([InlineKeyboardButton(f"🔥 Осталось: {remaining} попыток", callback_data="noop")])
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username or "Пользователь")
    reset_daily(user.id)
    await update.message.reply_text(
        f"🤖 **NeonFace**\n\n"
        "🎨 Аватарки | 📝 Текст | 🌤 Погода | 💡 Идеи | 🌟 Цитаты | 💬 Советы\n"
        "💞 Совместимость | 📅 Праздники | 💱 Конвертер | 🌟 Гороскоп | 🍳 Рецепты\n\n"
        f"🔥 Бесплатно: **{FREE_ATTEMPTS}** попыток в день\n"
        f"💎 Премиум: **безлимит** на 15 дней\n"
        f"💰 Цена: **{PREMIUM_PRICE} Stars** (~50₽)\n\n"
        "❓ Если нужна помощь — нажми '❓ Помощь' или напиши /help\n"
        "📩 Если нашёл баг — нажми '📩 Обратная связь'",
        reply_markup=main_menu(user.id),
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(get_help_menu(), parse_mode="Markdown", reply_markup=main_menu(user_id))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except:
        await query.message.reply_text("⏳ Кнопка устарела", reply_markup=main_menu(update.effective_user.id))
        return ConversationHandler.END
    
    user_id = query.from_user.id
    reset_daily(user_id)
    user_data = get_user(user_id)
    if not user_data:
        is_premium = False
        avatar_count = 0
        remaining = FREE_ATTEMPTS
        days_left = 0
    else:
        avatar_count, premium, premium_until = user_data
        is_premium = premium == 1 and premium_until > int(time.time())
        days_left = max(0, (premium_until - int(time.time())) // 86400) if is_premium else 0
        remaining = "∞" if is_premium else max(0, FREE_ATTEMPTS - avatar_count)

    if query.data == "create":
        if not is_premium and avatar_count >= FREE_ATTEMPTS:
            await query.message.reply_text("❌ **Бесплатные попытки кончились!**", reply_markup=main_menu(user_id))
            return ConversationHandler.END
        await query.message.reply_text("🎨 **Напиши, что хочешь увидеть**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]]))
        return WAITING_PROMPT

    elif query.data == "text_gen":
        await query.message.reply_text("📝 **Напиши тему:** идеи, пост, статья, сценарий", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]]))
        return WAITING_TEXT_PROMPT

    elif query.data == "weather":
        await query.message.reply_text("🌤 **Напиши город**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]]))
        return WAITING_CITY

    elif query.data == "idea":
        await query.message.reply_text(f"💡 **Идея дня:**\n\n{get_idea()}", reply_markup=main_menu(user_id))
        return ConversationHandler.END

    elif query.data == "quote":
        await query.message.reply_text(f"🌟 **Цитата дня:**\n\n{get_quote()}", reply_markup=main_menu(user_id))
        return ConversationHandler.END

    elif query.data == "advice":
        await query.message.reply_text(f"💬 **Совет дня:**\n\n{get_advice()}", reply_markup=main_menu(user_id))
        return ConversationHandler.END

    elif query.data == "compat":
        await query.message.reply_text("💞 **Напиши два имени через пробел**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]]))
        return WAITING_PROMPT

    elif query.data == "holidays":
        await query.message.reply_text(f"📅 **Праздники сегодня:**\n\n{get_holidays()}", reply_markup=main_menu(user_id))
        return ConversationHandler.END

    elif query.data == "currency":
        await query.message.reply_text("💱 **Напиши:** `100 usd rub`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]]))
        return WAITING_CURRENCY

    elif query.data == "horoscope":
        await query.message.reply_text("🌟 **Напиши знак зодиака:** овен, телец, близнецы...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]]))
        return WAITING_HOROSCOPE

    elif query.data == "recipe":
        await query.message.reply_text("🍳 **Что хочешь приготовить?** блины, омлет, борщ...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]]))
        return WAITING_RECIPE

    elif query.data == "premium_menu":
        await query.message.reply_text(f"💎 **Премиум**\n✅ Безлимит\n✅ 15 дней\n💰 {PREMIUM_PRICE} Stars", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Оплатить", callback_data="pay_stars")], [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]))

    elif query.data == "stats":
        status = "💎 Премиум" if is_premium else "🆓 Бесплатный"
        await query.message.reply_text(f"📊 **Статистика**\nСтатус: {status}\nСоздано: {avatar_count}\nОсталось: {remaining}\nДней премиума: {days_left}", reply_markup=main_menu(user_id))

    elif query.data == "help":
        await query.message.reply_text(get_help_menu(), parse_mode="Markdown", reply_markup=main_menu(user_id))
        return ConversationHandler.END

    elif query.data == "feedback":
        await query.message.reply_text(
            get_feedback_menu(),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🐛 Баг", callback_data="feedback_bug")],
                [InlineKeyboardButton("💡 Предложение", callback_data="feedback_idea")],
                [InlineKeyboardButton("❓ Вопрос", callback_data="feedback_question")],
                [InlineKeyboardButton("📝 Другое", callback_data="feedback_other")],
                [InlineKeyboardButton("↩️ Назад", callback_data="main_menu")]
            ])
        )
        return ConversationHandler.END

    elif query.data.startswith("feedback_"):
        feedback_type = query.data.replace("feedback_", "")
        context.user_data['feedback_type'] = feedback_type
        
        type_names = {
            "bug": "🐛 Баг",
            "idea": "💡 Предложение",
            "question": "❓ Вопрос",
            "other": "📝 Другое"
        }
        
        await query.message.reply_text(
            f"📝 **Вы выбрали: {type_names.get(feedback_type, 'Другое')}**\n\n"
            "✏️ **Напиши подробно, что случилось или что ты хочешь предложить.**\n\n"
            "Я передам это разработчику! 🔥",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]
            ])
        )
        return WAITING_FEEDBACK

    elif query.data == "main_menu":
        await query.message.reply_text("🤖 **Главное меню**", reply_markup=main_menu(user_id))

    elif query.data == "pay_stars":
        await query.message.reply_invoice(title="Премиум 15 дней", description="Безлимит всех функций", payload="premium_purchase", provider_token="", currency="XTR", prices=[LabeledPrice(label="Премиум", amount=PREMIUM_PRICE)], start_parameter="premium")

    return ConversationHandler.END

# ========== ОБРАБОТЧИКИ ==========

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    support_keywords = ["как", "что", "почему", "где", "сколько", "когда", "помощь", "помоги", "проблема", "не работает", "вопрос", "помощь", "цена", "премиум", "попытки", "блокировка", "аватарка", "погода", "рецепты", "гороскоп", "конвертер", "совместимость", "праздники"]
    if any(keyword in text.lower() for keyword in support_keywords):
        result = get_support_answer(text)
        await update.message.reply_text(result, parse_mode="Markdown", reply_markup=main_menu(user_id))
        return ConversationHandler.END
    
    parts = text.strip().split()
    if len(parts) == 2 and not any(c.isdigit() for c in text):
        result = get_compatibility(parts[0], parts[1])
        await update.message.reply_text(result, parse_mode="Markdown", reply_markup=main_menu(user_id))
        return ConversationHandler.END
    
    reset_daily(user_id)
    user_data = get_user(user_id)
    if not user_data:
        is_premium = False
        avatar_count = 0
    else:
        avatar_count, premium, premium_until = user_data
        is_premium = premium == 1 and premium_until > int(time.time())

    if not is_premium and avatar_count >= FREE_ATTEMPTS:
        await update.message.reply_text("❌ **Бесплатные попытки кончились!**", reply_markup=main_menu(user_id))
        return ConversationHandler.END

    await update.message.reply_text("🎨 **Генерирую...** ⏳ 5-10 сек")
    path = generate_avatar(text)
    if path:
        update_user_count(user_id)
        save_order(user_id, path)
        remaining_after = FREE_ATTEMPTS - (avatar_count + 1)
        if remaining_after < 0:
            remaining_after = 0
        with open(path, 'rb') as photo:
            await update.message.reply_photo(photo, caption=f"✅ **Готово!**\n🔥 Осталось: {remaining_after if not is_premium else '∞'}", reply_markup=main_menu(user_id))
        os.remove(path)
    else:
        await update.message.reply_text("❌ Ошибка! Попробуй другой текст.", reply_markup=main_menu(user_id))
    return ConversationHandler.END

async def handle_text_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    reset_daily(user_id)
    user_data = get_user(user_id)
    if not user_data:
        is_premium = False
        avatar_count = 0
    else:
        avatar_count, premium, premium_until = user_data
        is_premium = premium == 1 and premium_until > int(time.time())
    if not is_premium and avatar_count >= FREE_ATTEMPTS:
        await update.message.reply_text("❌ **Бесплатные попытки кончились!**", reply_markup=main_menu(user_id))
        return ConversationHandler.END
    result = generate_text(text)
    if result:
        update_user_count(user_id)
        remaining_after = FREE_ATTEMPTS - (avatar_count + 1)
        if remaining_after < 0:
            remaining_after = 0
        await update.message.reply_text(f"📝 **Текст:**\n\n{result}\n\n🔥 Осталось: {remaining_after if not is_premium else '∞'}", reply_markup=main_menu(user_id))
    else:
        await update.message.reply_text("❌ Ошибка!", reply_markup=main_menu(user_id))
    return ConversationHandler.END

async def handle_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    user_id = update.effective_user.id
    reset_daily(user_id)
    user_data = get_user(user_id)
    if not user_data:
        is_premium = False
        avatar_count = 0
    else:
        avatar_count, premium, premium_until = user_data
        is_premium = premium == 1 and premium_until > int(time.time())
    if not is_premium and avatar_count >= FREE_ATTEMPTS:
        await update.message.reply_text("❌ **Бесплатные попытки кончились!**", reply_markup=main_menu(user_id))
        return ConversationHandler.END
    result = get_weather(city)
    if result:
        update_user_count(user_id)
        remaining_after = FREE_ATTEMPTS - (avatar_count + 1)
        if remaining_after < 0:
            remaining_after = 0
        await update.message.reply_text(f"🌤 **Погода в {city}:**\n\n{result}\n\n🔥 Осталось: {remaining_after if not is_premium else '∞'}", reply_markup=main_menu(user_id))
    else:
        await update.message.reply_text("❌ Город не найден! Попробуй на английском (Moscow)", reply_markup=main_menu(user_id))
    return ConversationHandler.END

async def handle_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    parts = text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ Формат: `100 usd rub`", parse_mode="Markdown", reply_markup=main_menu(user_id))
        return ConversationHandler.END
    try:
        amount = float(parts[0])
        from_cur = parts[1].upper()
        to_cur = parts[2].upper()
    except:
        await update.message.reply_text("❌ Ошибка! Пример: `100 usd rub`", reply_markup=main_menu(user_id))
        return ConversationHandler.END
    result = convert_currency(amount, from_cur, to_cur)
    if result:
        await update.message.reply_text(result, parse_mode="Markdown", reply_markup=main_menu(user_id))
    else:
        await update.message.reply_text("❌ Ошибка конвертации! Проверь валюты", reply_markup=main_menu(user_id))
    return ConversationHandler.END

async def handle_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sign = update.message.text
    user_id = update.effective_user.id
    result = get_horoscope(sign)
    await update.message.reply_text(result, reply_markup=main_menu(user_id))
    return ConversationHandler.END

async def handle_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    user_id = update.effective_user.id
    result = get_recipe(query)
    await update.message.reply_text(result, reply_markup=main_menu(user_id))
    return ConversationHandler.END

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username or "Без имени"
    feedback_type = context.user_data.get('feedback_type', 'other')
    
    print(f"📩 Получена обратная связь от {username} (ID: {user_id})")
    print(f"📌 Тип: {feedback_type}")
    print(f"📝 Текст: {text}")
    
    success = save_feedback(user_id, username, text, feedback_type)
    
    if success:
        await update.message.reply_text(
            "✅ **Спасибо за обратную связь!**\n\n"
            "Твоё сообщение передано разработчику.\n"
            "Мы постараемся исправить всё как можно быстрее! 🔥\n\n"
            "💬 Если хочешь что-то добавить — напиши ещё раз!",
            reply_markup=main_menu(user_id)
        )
    else:
        await update.message.reply_text(
            "❌ **Ошибка при отправке!**\n\n"
            "Попробуй ещё раз или напиши разработчику напрямую: @ваш_ник",
            reply_markup=main_menu(user_id)
        )
    
    return ConversationHandler.END

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_premium(user_id, 15)
    await update.message.reply_text("💎 **Премиум активирован!**", reply_markup=main_menu(user_id))

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("❌ **Отменено!**", reply_markup=main_menu(user_id))
    return ConversationHandler.END

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern="^create$"),
            CallbackQueryHandler(button_handler, pattern="^text_gen$"),
            CallbackQueryHandler(button_handler, pattern="^weather$"),
            CallbackQueryHandler(button_handler, pattern="^compat$"),
            CallbackQueryHandler(button_handler, pattern="^currency$"),
            CallbackQueryHandler(button_handler, pattern="^horoscope$"),
            CallbackQueryHandler(button_handler, pattern="^recipe$"),
            CallbackQueryHandler(button_handler, pattern="^feedback$"),
            CallbackQueryHandler(button_handler, pattern="^feedback_"),
        ],
        states={
            WAITING_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt)],
            WAITING_TEXT_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_prompt)],
            WAITING_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_weather)],
            WAITING_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_currency)],
            WAITING_HOROSCOPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_horoscope)],
            WAITING_RECIPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_recipe)],
            WAITING_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success))
    
    print("✅ Бот запущен!")
    print("🎨 Аватарка | 📝 Текст | 🌤 Погода | 💡 Идея | 🌟 Цитата | 💬 Совет")
    print("💞 Совместимость | 📅 Праздники | 💱 Конвертер | 🌟 Гороскоп | 🍳 Рецепты")
    print("❓ Поддержка | 📩 Обратная связь")
    app.run_polling()

if __name__ == "__main__":
    main()