from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# 🔑 ضع توكن البوت هنا
BOT_TOKEN = "8495189316:AAGAzS9MTMfal703P-ncF7xMedg2RxqMBbo"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("ℹ️ معلومات", callback_data="info"),
            InlineKeyboardButton("❓ مساعدة", callback_data="help")
        ],
        [
            InlineKeyboardButton("📞 تواصل", callback_data="contact")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 أهلاً بك في البوت!\n\nاختر أحد الأزرار 👇",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "info":
        await query.edit_message_text("ℹ️ هذا بوت تجريبي مجاني بدون إعلانات.")

    elif query.data == "help":
        await query.edit_message_text("❓ استخدم /start لإظهار الأزرار.")

    elif query.data == "contact":
        await query.edit_message_text("📞 تواصل معنا عبر: @YourUsername")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
