from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler, ConversationHandler
from config import BOT_TOKEN, PREMIUM_PRICE, FREE_ATTEMPTS
from ai_generator import generate_avatar
from database import init_db, get_user, add_user, update_user_count, set_premium, reset_daily, check_premium, save_order
import os

WAITING_PROMPT = 1

def main_menu(is_premium=False, remaining=0):
    keyboard = [
        [InlineKeyboardButton("🎨 Создать аватарку", callback_data="create")],
        [InlineKeyboardButton("💎 Премиум", callback_data="premium_menu")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
    ]
    if not is_premium:
        keyboard.append([InlineKeyboardButton(f"🔥 Осталось: {remaining} попыток", callback_data="noop")])
    else:
        keyboard.append([InlineKeyboardButton("🔥 Премиум активен ♾️", callback_data="noop")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username or "Пользователь")
    reset_daily(user.id)
    
    is_premium = check_premium(user.id)
    user_data = get_user(user.id)
    avatar_count = user_data[0] if user_data else 0
    remaining = FREE_ATTEMPTS - avatar_count
    if remaining < 0:
        remaining = 0

    await update.message.reply_text(
        f"🤖 **Привет, {user.username or 'друг'}!**\n\n"
        "Я создаю **реалистичные аватарки** через нейросеть!\n\n"
        f"🔥 Бесплатно: **{remaining}** аватарок сегодня\n"
        f"💎 Премиум: **безлимит** на 15 дней\n"
        f"💰 Цена: **{PREMIUM_PRICE} Stars** (~50₽)\n\n"
        "👇 **Нажми на кнопку, чтобы начать!**",
        reply_markup=main_menu(is_premium, remaining),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    reset_daily(user_id)
    is_premium = check_premium(user_id)
    user_data = get_user(user_id)
    avatar_count = user_data[0] if user_data else 0
    remaining = FREE_ATTEMPTS - avatar_count
    if remaining < 0:
        remaining = 0

    if query.data == "create":
        if not is_premium and avatar_count >= FREE_ATTEMPTS:
            # Используем reply_text вместо edit_text
            await query.message.reply_text(
                "❌ **Бесплатные попытки кончились!**\n\n"
                f"💎 Купи премиум за **{PREMIUM_PRICE} Stars** и получи безлимит!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Купить премиум", callback_data="premium_menu")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        await query.message.reply_text(
            "🎨 **Напиши, что хочешь увидеть на аватарке**\n\n"
            "Примеры:\n"
            "• Девушка с голубыми волосами\n"
            "• Парень в капюшоне\n"
            "• Милый котик\n"
            "• Космический воин\n\n"
            "Чем подробнее — тем круче результат! 🔥\n\n"
            "✏️ Просто напиши текст в чат",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]
            ]),
            parse_mode="Markdown"
        )
        return WAITING_PROMPT

    elif query.data == "again":
        await query.message.reply_text(
            "🎨 **Напиши, что хочешь увидеть на аватарке**\n\n"
            "Примеры:\n"
            "• Девушка с голубыми волосами\n"
            "• Парень в капюшоне\n"
            "• Милый котик\n\n"
            "✏️ Просто напиши текст в чат",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]
            ]),
            parse_mode="Markdown"
        )
        return WAITING_PROMPT

    elif query.data == "premium_menu":
        await query.message.reply_text(
            f"💎 **Премиум доступ**\n\n"
            "Что ты получаешь:\n"
            "✅ **Безлимит** аватарок\n"
            "✅ **HD качество**\n"
            "✅ На **15 дней**\n\n"
            f"💰 **Цена: {PREMIUM_PRICE} Stars** (~50₽)\n\n"
            "Нажми на кнопку ниже для оплаты",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Оплатить Stars", callback_data="pay_stars")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]),
            parse_mode="Markdown"
        )

    elif query.data == "stats":
        status = "💎 Премиум" if is_premium else "🆓 Бесплатный"
        remaining_text = "∞ (безлимит)" if is_premium else remaining
        await query.message.reply_text(
            f"📊 **Твоя статистика**\n\n"
            f"Статус: **{status}**\n"
            f"Создано аватарок: **{avatar_count}**\n"
            f"Осталось сегодня: **{remaining_text}**\n\n"
            f"💬 Напиши текст или нажми на кнопку!",
            reply_markup=main_menu(is_premium, remaining),
            parse_mode="Markdown"
        )

    elif query.data == "main_menu":
        await query.message.reply_text(
            f"🤖 **Главное меню**\n\n"
            f"🔥 Бесплатно: **{remaining}** аватарок сегодня\n"
            f"💎 Премиум: **безлимит** на 15 дней\n"
            f"💰 Цена: **{PREMIUM_PRICE} Stars** (~50₽)\n\n"
            "👇 **Выбери действие:**",
            reply_markup=main_menu(is_premium, remaining),
            parse_mode="Markdown"
        )

    elif query.data == "pay_stars":
        await query.message.reply_invoice(
            title="Премиум 15 дней",
            description="Безлимитные аватарки через нейросеть",
            payload="premium_purchase",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Премиум", amount=PREMIUM_PRICE)],
            start_parameter="premium"
        )

    return ConversationHandler.END

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    user_id = update.effective_user.id
    
    reset_daily(user_id)
    is_premium = check_premium(user_id)
    user_data = get_user(user_id)
    avatar_count = user_data[0] if user_data else 0

    if not is_premium and avatar_count >= FREE_ATTEMPTS:
        await update.message.reply_text(
            "❌ **Бесплатные попытки кончились!**\n\n"
            f"💎 Купи премиум за **{PREMIUM_PRICE} Stars**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 Купить премиум", callback_data="premium_menu")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🧠 **Генерирую аватарку через нейросеть...**\n"
        "⏳ Это может занять 5-10 секунд\n"
        "🔥 Результат будет 🔥"
    )

    path = generate_avatar(prompt)

    if path:
        update_user_count(user_id)
        save_order(user_id, path)
        
        remaining_after = FREE_ATTEMPTS - (avatar_count + 1)
        if remaining_after < 0:
            remaining_after = 0
            
        with open(path, 'rb') as photo:
            await update.message.reply_photo(
                photo,
                caption=f"✅ **Аватарка готова!**\n\n"
                        f"📝 Запрос: **{prompt[:50]}**\n"
                        f"🔥 Осталось: **{remaining_after if not is_premium else '∞'}** аватарок\n\n"
                        f"💬 Напиши новый текст или нажми на кнопку!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎨 Ещё аватарку", callback_data="again")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]),
                parse_mode="Markdown"
            )
        os.remove(path)
    else:
        await update.message.reply_text(
            "❌ **Ошибка генерации!**\n\n"
            "Попробуй написать другой текст.\n"
            "💡 Совет: опиши подробнее на английском",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="create")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ])
        )

    return ConversationHandler.END

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_premium(user_id, 15)
    await update.message.reply_text(
        "💎 **Поздравляем! Премиум активирован!**\n\n"
        "Теперь у тебя **безлимит** на 15 дней!\n\n"
        "🔥 Просто пиши текст и получай аватарки!",
        reply_markup=main_menu(True, 0),
        parse_mode="Markdown"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ **Отменено!**",
        reply_markup=main_menu(False, 0),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern="^create$"),
            CallbackQueryHandler(button_handler, pattern="^again$")
        ],
        states={
            WAITING_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(button_handler, pattern="^main_menu$")
        ]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success))
    
    print("✅ Бот запущен!")
    print(f"💎 Премиум: {PREMIUM_PRICE} Stars / 15 дней")
    print(f"🔥 Бесплатно: {FREE_ATTEMPTS} аватарок в день")
    print("🎨 Кнопка 'Создать аватарку' в меню")
    app.run_polling()

if __name__ == "__main__":
    main()