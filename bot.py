from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# =======================
# 🔑 التوكن الخاص بالبوت
BOT_TOKEN = 8495189316:AAGAzS9MTMfal703P-ncF7xMedg2RxqMBbo

# 🛡️ رقم أدمن البوت (أنت فقط)
ADMIN_ID = 643482335# ضع رقمك هنا

# =======================
# النصوص الخاصة بالأزرار
# يمكنك إضافة زر جديد أو حذف أي زر بسهولة هنا
BUTTON_REPLIES = {
    "info": "ℹ️ هذا نص المعلومات الافتراضي",
    "help": "❓ هذا نص المساعدة الافتراضي",
    "contact": "📞 هذا نص التواصل الافتراضي"
    # مثال لإضافة زر جديد:
    # "lectures": "📚 هذه نص المحاضرات"
}

# =======================
# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []

    # إنشاء الأزرار تلقائيًا من BUTTON_REPLIES
    for key, data in BUTTON_REPLIES.items():
        row.append(InlineKeyboardButton(data.split("\n")[0], callback_data=key))  # نأخذ أول سطر فقط كاسم الزر
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 أهلاً بك في البوت!\nاختر أحد الأزرار 👇",
        reply_markup=reply_markup
    )

# =======================
# التعامل مع الضغط على الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data in BUTTON_REPLIES:
        await query.edit_message_text(BUTTON_REPLIES[query.data])

# =======================
# أمر /set لتغيير نصوص الأزرار من داخل البوت (أنت فقط)
async def set_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("الاستخدام:\n/set info النص الجديد")
        return

    key = context.args[0]
    new_text = " ".join(context.args[1:])

    if key in BUTTON_REPLIES:
        BUTTON_REPLIES[key] = new_text
        await update.message.reply_text("✅ تم التعديل بنجاح")
    else:
        await update.message.reply_text("❌ هذا الزر غير موجود")

# =======================
# تشغيل البوت
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("set", set_text))
    print("البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
