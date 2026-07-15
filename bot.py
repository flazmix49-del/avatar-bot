from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler, ConversationHandler
from config import BOT_TOKEN, PREMIUM_PRICE, FREE_ATTEMPTS
from ai_generator import generate_avatar, generate_video, get_fact
from database import init_db, get_user, add_user, update_user_count, set_premium, reset_daily, check_premium, save_order, get_premium_days_left
import os
import random
import sqlite3
import time

# Состояния
WAITING_PROMPT = 1
WAITING_VIDEO = 2

def main_menu(is_premium=False, remaining=0, days_left=0):
    keyboard = [
        [
            InlineKeyboardButton("🎨 Аватарка", callback_data="create"),
            InlineKeyboardButton("🎬 Видео", callback_data="video_create")
        ],
        [
            InlineKeyboardButton("🔥 Факт дня", callback_data="fact"),
            InlineKeyboardButton("💎 Премиум", callback_data="premium_menu")
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            InlineKeyboardButton("🔄 Перезапустить", callback_data="main_menu")
        ]
    ]
    if not is_premium:
        keyboard.append([InlineKeyboardButton(f"🔥 Осталось: {remaining} попыток", callback_data="noop")])
    else:
        keyboard.append([InlineKeyboardButton(f"🔥 Премиум: {days_left} дней", callback_data="noop")])
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
    
    days_left = get_premium_days_left(user.id)

    await update.message.reply_text(
        f"🤖 **NeonFace**\n\n"
        "Создаю **аватарки** и **видео** через нейросеть!\n\n"
        f"🔥 Бесплатно: **{remaining}** попыток сегодня\n"
        f"💎 Премиум: **безлимит** на 15 дней\n"
        f"💰 Цена: **{PREMIUM_PRICE} Stars** (~50₽)",
        reply_markup=main_menu(is_premium, remaining, days_left),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    try:
        await query.answer()
    except:
        await query.message.reply_text("⏳ Кнопка устарела, нажми /start заново", reply_markup=main_menu(False, 0))
        return ConversationHandler.END
    
    user_id = query.from_user.id
    reset_daily(user_id)
    is_premium = check_premium(user_id)
    user_data = get_user(user_id)
    avatar_count = user_data[0] if user_data else 0
    remaining = FREE_ATTEMPTS - avatar_count
    if remaining < 0:
        remaining = 0
    days_left = get_premium_days_left(user_id)

    if query.data == "create":
        if not is_premium and avatar_count >= FREE_ATTEMPTS:
            await query.message.reply_text(
                "❌ **Бесплатные попытки кончились!**\n\n"
                f"💎 Купи премиум за **{PREMIUM_PRICE} Stars**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Купить премиум", callback_data="premium_menu")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]),
                parse_mode="Markdown"
            )
            return ConversationHandler.END
        
        await query.message.reply_text(
            "🎨 **Напиши, что хочешь увидеть на аватарке**\n\n"
            "Примеры: девушка с голубыми волосами, милый котик, космический воин\n\n"
            "✏️ Просто напиши текст в чат",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]
            ]),
            parse_mode="Markdown"
        )
        return WAITING_PROMPT

    elif query.data == "video_create":
        if not is_premium and avatar_count >= FREE_ATTEMPTS:
            await query.message.reply_text(
                "❌ **Бесплатные попытки кончились!**\n\n"
                f"💎 Купи премиум за **{PREMIUM_PRICE} Stars**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Купить премиум", callback_data="premium_menu")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]),
                parse_mode="Markdown"
            )
            return ConversationHandler.END
        
        await query.message.reply_text(
            "🎬 **Напиши, что хочешь увидеть в видео**\n\n"
            "Примеры: закат на море, город ночью, космический полёт\n\n"
            "⏳ Может занять 20-40 секунд",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]
            ]),
            parse_mode="Markdown"
        )
        return WAITING_VIDEO

    elif query.data == "fact":
        fact = get_fact()
        await query.message.reply_text(
            f"🔥 **Факт дня:**\n\n{fact}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 Ещё факт", callback_data="fact")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    elif query.data == "premium_menu":
        await query.message.reply_text(
            f"💎 **Премиум доступ**\n\n"
            "✅ Безлимит всех функций\n"
            "✅ HD качество\n"
            "✅ На 15 дней\n\n"
            f"💰 **{PREMIUM_PRICE} Stars** (~50₽)",
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
            f"📊 **Статистика**\n\n"
            f"Статус: **{status}**\n"
            f"Создано: **{avatar_count}**\n"
            f"Осталось: **{remaining_text}**\n"
            f"Дней премиума: **{days_left}**",
            reply_markup=main_menu(is_premium, remaining, days_left),
            parse_mode="Markdown"
        )

    elif query.data == "main_menu":
        await query.message.reply_text(
            f"🤖 **NeonFace**\n\n"
            f"🔥 Осталось: **{remaining}** попыток\n"
            f"💎 Премиум: безлимит на 15 дней\n"
            f"💰 Цена: **{PREMIUM_PRICE} Stars**",
            reply_markup=main_menu(is_premium, remaining, days_left),
            parse_mode="Markdown"
        )

    elif query.data == "pay_stars":
        await query.message.reply_invoice(
            title="Премиум 15 дней",
            description="Безлимит: аватарки, видео",
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
    
    await update.message.reply_text("🎨 **Генерирую аватарку...** ⏳ 5-10 секунд")
    
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

    path = generate_avatar(prompt)
    if path:
        update_user_count(user_id)
        save_order(user_id, path)
        remaining_after = FREE_ATTEMPTS - (avatar_count + 1)
        if remaining_after < 0:
            remaining_after = 0
        days_left = get_premium_days_left(user_id)
            
        with open(path, 'rb') as photo:
            await update.message.reply_photo(
                photo,
                caption=f"✅ **Аватарка готова!**\n\n"
                        f"📝 {prompt[:50]}\n"
                        f"🔥 Осталось: **{remaining_after if not is_premium else '∞'}** попыток",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎨 Ещё", callback_data="create")],
                    [InlineKeyboardButton("🎬 Видео", callback_data="video_create")],
                    [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]
                ]),
                parse_mode="Markdown"
            )
        os.remove(path)
    else:
        await update.message.reply_text("❌ Ошибка! Попробуй другой текст.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]
        ]))

    return ConversationHandler.END

async def handle_video_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    user_id = update.effective_user.id
    
    await update.message.reply_text("🎬 **Генерирую видео...** ⏳ 20-40 секунд")
    
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

    path = generate_video(prompt)
    if path:
        update_user_count(user_id)
        save_order(user_id, path)
        remaining_after = FREE_ATTEMPTS - (avatar_count + 1)
        if remaining_after < 0:
            remaining_after = 0
            
        with open(path, 'rb') as video:
            await update.message.reply_video(
                video,
                caption=f"✅ **Видео готово!**\n\n"
                        f"📝 {prompt[:50]}\n"
                        f"🔥 Осталось: **{remaining_after if not is_premium else '∞'}** попыток",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎬 Ещё", callback_data="video_create")],
                    [InlineKeyboardButton("🎨 Аватарка", callback_data="create")],
                    [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]
                ]),
                parse_mode="Markdown"
            )
        os.remove(path)
    else:
        await update.message.reply_text(
            "❌ **Ошибка генерации видео!**\n\n"
            "Попробуй другой текст.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎨 Аватарка", callback_data="create")],
                [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]
            ])
        )

    return ConversationHandler.END

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_premium(user_id, 15)
    days_left = get_premium_days_left(user_id)
    await update.message.reply_text(
        "💎 **Поздравляем! Премиум активирован!**\n\n"
        f"🔥 Премиум активен на **{days_left}** дней!\n\n"
        "Создавай аватарки и видео безлимитно!",
        reply_markup=main_menu(True, 0, days_left),
        parse_mode="Markdown"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ **Отменено!**",
        reply_markup=main_menu(False, 0, 0),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern="^create$"),
            CallbackQueryHandler(button_handler, pattern="^video_create$"),
        ],
        states={
            WAITING_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt)],
            WAITING_VIDEO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_prompt)],
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
    print(f"🔥 Бесплатно: {FREE_ATTEMPTS} попыток в день")
    print("🎨 Аватарка | 🎬 Видео | 🔥 Факт дня")
    app.run_polling()

if __name__ == "__main__":
    main()