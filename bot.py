from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import os
import json

BOT_TOKEN = "8495189316:AAGAzS9MTMfal703P-ncF7xMedg2RxqMBbo"  # ضع توكن البوت هنا
ADMIN_ID = 643482335  # ضع رقمك هنا

# ==========================
# بيانات البوت
DATA_FILE = "buttons.json"
USERS_FILE = "users.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        BUTTON_REPLIES = json.load(f)
else:
    BUTTON_REPLIES = {}

if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        USERS = json.load(f)
else:
    USERS = {}

TEMP_CATEGORY = None
TEMP_KEY = None
TEMP_FILE = None
EDIT_CATEGORY = None
EDIT_KEY = None
EDIT_OPTION = None
CURRENT_MENU = "main"

# ==========================
def save_buttons():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(BUTTON_REPLIES, f, ensure_ascii=False, indent=2)

def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(USERS, f, ensure_ascii=False, indent=2)

# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

# ==========================
async def show_main_menu(update, context, message=None):
    keyboard = []
    row = []

    # أزرار الفئات للطلاب
    for category in BUTTON_REPLIES.keys():
        row.append(InlineKeyboardButton(category, callback_data=f"cat_{category}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # أزرار الأدمن
    if update.effective_user.id == ADMIN_ID:
        admin_row = [
            InlineKeyboardButton("➕ إضافة فئة جديدة", callback_data="add_category"),
            InlineKeyboardButton("📝 تعديل فئة/زر", callback_data="edit_category"),
            InlineKeyboardButton("❌ حذف فئة/زر", callback_data="delete_category"),
            InlineKeyboardButton("📊 إحصائيات البوت", callback_data="stats")
        ]
        keyboard.append(admin_row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "👋 أهلاً! اختر فئة 👇" if update.effective_user.id != ADMIN_ID else "👑 واجهة الأدمن: اختر فئة أو إدارة"
    if message:
        await message.edit_text(text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

# ==========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TEMP_CATEGORY, TEMP_KEY, TEMP_FILE, EDIT_CATEGORY, EDIT_KEY, EDIT_OPTION
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # تسجيل مستخدم جديد
    if str(user_id) not in USERS:
        USERS[str(user_id)] = {"username": query.from_user.username,
                               "first_name": query.from_user.first_name,
                               "last_name": query.from_user.last_name or ""}
        save_users()
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🆕 مستخدم جديد دخل البوت:\nID: {user_id}\nيوزر: @{query.from_user.username}\nالاسم: {query.from_user.first_name} {query.from_user.last_name or ''}"
        )

    # --------------------
    # أزرار الأدمن
    if user_id == ADMIN_ID:
        if data == "add_category":
            TEMP_CATEGORY = None
            await query.message.reply_text("✏️ أرسل اسم الفئة الجديدة:")
            return
        elif data == "edit_category":
            keyboard = [[InlineKeyboardButton(cat, callback_data=f"editcat_{cat}")] for cat in BUTTON_REPLIES.keys()]
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
            await query.message.reply_text("اختر الفئة لتعديلها:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data == "delete_category":
            keyboard = [[InlineKeyboardButton(cat, callback_data=f"delcat_{cat}")] for cat in BUTTON_REPLIES.keys()]
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
            await query.message.reply_text("اختر الفئة للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data == "stats":
            num_users = len(USERS)
            num_categories = len(BUTTON_REPLIES)
            total_buttons = sum(len(v) for v in BUTTON_REPLIES.values())
            usernames = [f"@{v['username']}" for v in USERS.values() if v['username']]
            stats_text = f"📊 إحصائيات البوت:\nعدد المستخدمين: {num_users}\nعدد الفئات: {num_categories}\nعدد الأزرار: {total_buttons}\nالمستخدمون:\n" + "\n".join(usernames)
            await query.message.reply_text(stats_text)
            return

        elif data.startswith("editcat_"):
            EDIT_CATEGORY = data.replace("editcat_", "")
            keyboard = [[InlineKeyboardButton("➕ إضافة زر جديد", callback_data="add_button")],
                        [InlineKeyboardButton("📝 تعديل زر موجود", callback_data="edit_button")],
                        [InlineKeyboardButton("❌ حذف زر", callback_data="delete_button")],
                        [InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
            await query.message.reply_text(f"اختر العملية للفئة '{EDIT_CATEGORY}':", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        elif data.startswith("delcat_"):
            del_cat = data.replace("delcat_", "")
            if del_cat in BUTTON_REPLIES:
                BUTTON_REPLIES.pop(del_cat)
                save_buttons()
                await query.message.reply_text(f"✅ تم حذف الفئة '{del_cat}' بنجاح")
            return

        elif data in ["add_button", "edit_button", "delete_button"]:
            if data == "add_button":
                TEMP_KEY = None
                TEMP_FILE = None
                await query.message.reply_text(f"✏️ أرسل اسم الزر الجديد للفئة '{EDIT_CATEGORY}':")
            elif data == "edit_button":
                keyboard = [[InlineKeyboardButton(k, callback_data=f"editbtn_{k}")] for k in BUTTON_REPLIES.get(EDIT_CATEGORY, {}).keys()]
                keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
                await query.message.reply_text("اختر الزر لتعديله:", reply_markup=InlineKeyboardMarkup(keyboard))
            elif data == "delete_button":
                keyboard = [[InlineKeyboardButton(k, callback_data=f"delbtn_{k}")] for k in BUTTON_REPLIES.get(EDIT_CATEGORY, {}).keys()]
                keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
                await query.message.reply_text("اختر الزر للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        elif data.startswith("editbtn_"):
            EDIT_KEY = data.replace("editbtn_", "")
            keyboard = [
                [InlineKeyboardButton("تعديل الاسم", callback_data="edit_name")],
                [InlineKeyboardButton("تعديل النص", callback_data="edit_text")],
                [InlineKeyboardButton("تعديل الملف", callback_data="edit_file")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ]
            await query.message.reply_text(f"اختر ما تريد تعديله للزر '{EDIT_KEY}':", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        elif data.startswith("delbtn_"):
            del_key = data.replace("delbtn_", "")
            if del_key in BUTTON_REPLIES.get(EDIT_CATEGORY, {}):
                BUTTON_REPLIES[EDIT_CATEGORY].pop(del_key)
                save_buttons()
                await query.message.reply_text(f"✅ تم حذف الزر '{del_key}' بنجاح")
            return

        elif data in ["edit_name", "edit_text", "edit_file"]:
            EDIT_OPTION = data.split("_")[1]
            prompt = "✏️ أرسل الاسم الجديد:" if EDIT_OPTION=="name" else "✏️ أرسل النص الجديد:" if EDIT_OPTION=="text" else "📄 أرسل ملف PDF الجديد:"
            await query.message.reply_text(prompt)
            return

        elif data == "back":
            TEMP_CATEGORY = None
            TEMP_KEY = None
            EDIT_CATEGORY = None
            EDIT_KEY = None
            EDIT_OPTION = None
            await show_main_menu(update, context)
            return

    # --------------------
    # أزرار الطلاب
    if data.startswith("cat_"):
        category = data.replace("cat_", "")
        keyboard = [[InlineKeyboardButton(k, callback_data=f"userbtn_{category}_{k}")] for k in BUTTON_REPLIES.get(category, {}).keys()]
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
        await query.message.edit_text(f"📂 فئة: {category}", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("userbtn_"):
        parts = data.replace("userbtn_", "").split("_",1)
        category = parts[0]
        key = parts[1]
        info = BUTTON_REPLIES.get(category, {}).get(key, {})
        if info.get("file"):
            await query.message.reply_document(InputFile(info["file"]), caption=info.get("text",""))
        else:
            await query.message.edit_text(info.get("text",""))

# ==========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TEMP_CATEGORY, TEMP_KEY, TEMP_FILE, EDIT_CATEGORY, EDIT_KEY, EDIT_OPTION
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    # استقبال ملف PDF
    if update.message.document:
        TEMP_FILE = await update.message.document.get_file()
        os.makedirs("files", exist_ok=True)
        file_path = f"files/{update.message.document.file_name}"
        await TEMP_FILE.download_to_drive(file_path)
        TEMP_FILE = file_path

        if EDIT_OPTION=="file" and EDIT_CATEGORY and EDIT_KEY:
            BUTTON_REPLIES[EDIT_CATEGORY][EDIT_KEY]["file"] = TEMP_FILE
            save_buttons()
            EDIT_OPTION = None
            EDIT_KEY = None
            await update.message.reply_text("✅ تم تعديل الملف بنجاح!")
        else:
            await update.message.reply_text("✅ الملف محفوظ، أرسل النص ليكمل الزر.")
        return

    # إضافة فئة جديدة
    if TEMP_CATEGORY is None and EDIT_CATEGORY is None:
        TEMP_CATEGORY = update.message.text
        if TEMP_CATEGORY not in BUTTON_REPLIES:
            BUTTON_REPLIES[TEMP_CATEGORY] = {}
            save_buttons()
            await update.message.reply_text(f"✅ تم إنشاء الفئة '{TEMP_CATEGORY}' بنجاح! الآن اضغط /start لإضافة أزرار داخلها.")
        TEMP_CATEGORY = None
        return

    # إضافة زر جديد داخل فئة
    if EDIT_CATEGORY and TEMP_KEY is None and EDIT_OPTION is None:
        TEMP_KEY = update.message.text
        await update.message.reply_text(f"✅ الاسم محفوظ. أرسل النص الذي تريد عرضه عند الضغط على الزر '{TEMP_KEY}':")
        return

    if EDIT_CATEGORY and TEMP_KEY and not EDIT_OPTION:
        BUTTON_REPLIES[EDIT_CATEGORY][TEMP_KEY] = {"text": update.message.text, "file": TEMP_FILE}
        TEMP_KEY = None
        TEMP_FILE = None
        save_buttons()
        await update.message.reply_text("✅ تم حفظ الزر بنجاح! استخدم /start لرؤية الزر الجديد.")
        return

    # تعديل زر موجود
    if EDIT_CATEGORY and EDIT_KEY and EDIT_OPTION:
        if EDIT_OPTION=="name":
            BUTTON_REPLIES[EDIT_CATEGORY][update.message.text] = BUTTON_REPLIES[EDIT_CATEGORY].pop(EDIT_KEY)
        elif EDIT_OPTION=="text":
            BUTTON_REPLIES[EDIT_CATEGORY][EDIT_KEY]["text"] = update.message.text
        EDIT_KEY = None
        EDIT_OPTION = None
        save_buttons()
        await update.message.reply_text("✅ تم تعديل الزر بنجاح!")

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
