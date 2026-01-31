from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import os

BOT_TOKEN = "8495189316:AAGAzS9MTMfal703P-ncF7xMedg2RxqMBbo"  # ضع التوكن هنا
ADMIN_ID = 643482335  # ضع رقمك هنا

# ==========================
# نصوص الأزرار والملفات
BUTTON_REPLIES = {
    "info": {"text": "ℹ️ معلومات عن البوت: مجاني للطلاب", "file": None},
    "help": {"text": "❓ تعليمات: اضغط على الأزرار لاختيار المحاضرات أو التواصل", "file": None},
    "contact": {"text": "📞 للتواصل: @YourUsername", "file": None}
}

TEMP_KEY = None  # مؤقت للاسم الداخلي
TEMP_FILE = None  # مؤقت للملف المرفوع

# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []

    # إضافة أزرار الطلاب
    for key, data in BUTTON_REPLIES.items():
        row.append(InlineKeyboardButton(data["text"].split("\n")[0], callback_data=key))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # أزرار الأدمن
    if update.effective_user.id == ADMIN_ID:
        admin_row = [
            InlineKeyboardButton("➕ إضافة زر جديد", callback_data="add_new"),
            InlineKeyboardButton("📝 تعديل زر موجود", callback_data="edit_existing"),
            InlineKeyboardButton("❌ حذف زر", callback_data="delete_existing")
        ]
        keyboard.append(admin_row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 أهلاً! اختر زرًا 👇", reply_markup=reply_markup)

# ==========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TEMP_KEY, TEMP_FILE
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # أزرار الأدمن
    if user_id == ADMIN_ID:
        if data == "add_new":
            TEMP_KEY = None
            TEMP_FILE = None
            await query.message.reply_text("✏️ أرسل اسم الزر الجديد:")
            return
        elif data == "edit_existing":
            await query.message.reply_text("✏️ أرسل الاسم الداخلي للزر الذي تريد تعديله:")
            return
        elif data == "delete_existing":
            await query.message.reply_text("✏️ أرسل الاسم الداخلي للزر الذي تريد حذفه:")
            return

    # زر موجود → إرسال النص أو الملف
    if data in BUTTON_REPLIES:
        info = BUTTON_REPLIES[data]
        if info["file"]:
            await query.message.reply_document(InputFile(info["file"]), caption=info["text"])
        else:
            await query.edit_message_text(info["text"])

# ==========================
# استقبال رسائل الأدمن للنصوص والملفات
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TEMP_KEY, TEMP_FILE
    user_id = update.effective_user.id
    text = update.message.text

    if user_id != ADMIN_ID:
        return

    # إذا أرسل ملف PDF
    if update.message.document:
        TEMP_FILE = await update.message.document.get_file()
        file_path = f"files/{update.message.document.file_name}"
        os.makedirs("files", exist_ok=True)
        await TEMP_FILE.download_to_drive(file_path)
        TEMP_FILE = file_path
        await update.message.reply_text(f"✅ تم رفع الملف '{update.message.document.file_name}'. أرسل النص الذي تريد عرضه مع الزر:")
        return

    # إذا لم يكن هناك اسم مؤقت → أخذ الاسم الداخلي للزر
    if TEMP_KEY is None:
        TEMP_KEY = text
        await update.message.reply_text(f"✅ الاسم محفوظ. الآن أرسل النص الذي تريد عرضه عند الضغط على الزر '{TEMP_KEY}':")
    else:
        # حفظ الزر الجديد أو التعديل
        BUTTON_REPLIES[TEMP_KEY] = {"text": text, "file": TEMP_FILE}
        TEMP_KEY = None
        TEMP_FILE = None
        await update.message.reply_text("✅ تم حفظ الزر بنجاح! استخدم /start لرؤية الزر الجديد.")

# ==========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))
    print("البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
