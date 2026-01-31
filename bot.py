from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import os, json, asyncio

# ========================== إعدادات البوت ==========================
BOT_TOKEN = "8460468406:AAGYBv7P5e-cwr-dG8rhJn4YU4MmEDfb-po"  # ضع التوكن هنا
MAIN_ADMIN_ID = 643482335  # أدمن رئيسي

DATA_FILE = "buttons.json"
USERS_FILE = "users.json"
ADMINS_FILE = "admins.json"

# ========================== تحميل البيانات ==========================
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

BUTTON_REPLIES = load_json(DATA_FILE, {})
USERS = load_json(USERS_FILE, {})
ADMINS = load_json(ADMINS_FILE, {str(MAIN_ADMIN_ID): {"permissions":["add","edit","delete","stats","manage_admins"]}})

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_buttons(): save_json(DATA_FILE, BUTTON_REPLIES)
def save_users(): save_json(USERS_FILE, USERS)
def save_admins(): save_json(ADMINS_FILE, ADMINS)

def split_button_text(text, max_len=20):
    if len(text) <= max_len: return text
    idx = text.rfind(" ",0,max_len)
    if idx==-1: idx=max_len
    return text[:idx] + "\n" + text[idx:].strip()

# ========================== متغيرات مؤقتة ==========================
TEMP_CATEGORY = None
TEMP_KEY = None
TEMP_FILE = None
EDIT_CATEGORY = None
EDIT_KEY = None

# ========================== تسجيل مستخدم جديد ==========================
async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) not in USERS:
        USERS[str(user_id)] = {
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
            "last_name": update.effective_user.last_name or ""
        }
        save_users()
        try:
            await context.bot.send_message(
                chat_id=MAIN_ADMIN_ID,
                text=(
                    f"🆕 مستخدم جديد دخل البوت:\n"
                    f"ID: {user_id}\n"
                    f"يوزر: @{update.effective_user.username}\n"
                    f"الاسم: {update.effective_user.first_name} {update.effective_user.last_name or ''}"
                )
            )
        except:
            pass

# ========================== واجهة رئيسية ==========================
async def show_main_menu(update, context, message=None):
    user_id = update.effective_user.id
    keyboard, row = [], []

    # أزرار الفئات
    for category in BUTTON_REPLIES.keys():
        row.append(InlineKeyboardButton(split_button_text(category), callback_data=f"cat_{category}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)

    # أزرار الأدمن
    if str(user_id) in ADMINS:
        admin_row = [
            InlineKeyboardButton("➕ إضافة فئة", callback_data="add_category"),
            InlineKeyboardButton("📝 تعديل فئة/زر", callback_data="edit_category"),
            InlineKeyboardButton("❌ حذف فئة/زر", callback_data="delete_category"),
            InlineKeyboardButton("📊 إحصائيات البوت", callback_data="stats"),
            InlineKeyboardButton("👑 إدارة الأدمن", callback_data="manage_admins")
        ]
        keyboard.append(admin_row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "👋 أهلاً! اختر فئة 👇" if str(user_id) not in ADMINS else "👑 واجهة الأدمن: اختر فئة أو إدارة"

    if message:
        await message.edit_text(text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

# ========================== /start ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await register_user(update, context)
    await show_main_menu(update, context)

# ========================== Handlers ==========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TEMP_CATEGORY, TEMP_KEY, TEMP_FILE, EDIT_CATEGORY, EDIT_KEY
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    await register_user(update, context)

    # العودة للقائمة الرئيسية
    if data == "back":
        await show_main_menu(update, context)
        return

    # اختيار فئة
    if data.startswith("cat_"):
        category = data.replace("cat_", "")
        keyboard = [[InlineKeyboardButton(split_button_text(k), callback_data=f"userbtn_{category}_{k}")] 
                    for k in BUTTON_REPLIES.get(category, {})]
        if str(user_id) in ADMINS:
            admin_row = [
                InlineKeyboardButton("➕ إضافة زر", callback_data=f"addbtn_{category}"),
                InlineKeyboardButton("📝 تعديل زر", callback_data=f"editbtn_{category}"),
                InlineKeyboardButton("❌ حذف زر", callback_data=f"delbtn_{category}"),
                InlineKeyboardButton("🗂 إضافة محتوى للزر", callback_data=f"addcontent_{category}")
            ]
            keyboard.append(admin_row)
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
        await query.message.edit_text(f"📂 فئة: {category}", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # اختيار زر المستخدم
    if data.startswith("userbtn_"):
        parts = data.replace("userbtn_", "").split("_",1)
        category, key = parts[0], parts[1]
        info = BUTTON_REPLIES.get(category, {}).get(key, {})
        if info.get("file"):
            file_path = info["file"]
            file_name = os.path.basename(file_path)
            try:
                await query.message.reply_document(InputFile(file_path, filename=file_name), caption=info.get("text",""))
            except:
                await query.message.reply_text(info.get("text",""))
        else:
            await query.message.edit_text(info.get("text",""))
        return

    # إدارة الأدمن: إضافة زر/تعديل/حذف/إضافة محتوى
    if str(user_id) in ADMINS:
        if data.startswith("addbtn_"):
            TEMP_CATEGORY = data.replace("addbtn_", "")
            TEMP_KEY = None
            await query.message.reply_text(f"✏️ أرسل اسم الزر الجديد في فئة {TEMP_CATEGORY}:")
            return
        if data.startswith("addcontent_"):
            TEMP_CATEGORY = data.replace("addcontent_", "")
            TEMP_KEY = None
            await query.message.reply_text(f"✏️ أرسل اسم الزر لإضافة محتوى له في فئة {TEMP_CATEGORY}:")
            return

# ---- استقبال الرسائل ----
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TEMP_CATEGORY, TEMP_KEY, TEMP_FILE
    user_id = update.effective_user.id
    if str(user_id) not in ADMINS:
        return

    # استقبال ملف PDF
    if update.message.document:
        TEMP_FILE = await update.message.document.get_file()
        os.makedirs("files", exist_ok=True)
        file_path = f"files/{update.message.document.file_name}"
        try:
            await TEMP_FILE.download_to_drive(file_path)
        except:
            await update.message.reply_text("❌ حدث خطأ أثناء رفع الملف.")
            return
        TEMP_FILE = file_path
        if TEMP_CATEGORY and TEMP_KEY:
            BUTTON_REPLIES[TEMP_CATEGORY][TEMP_KEY]["file"] = TEMP_FILE
            save_buttons()
        await update.message.reply_text("✅ تم رفع الملف بنجاح.")
        return

    # إضافة زر جديد
    if TEMP_CATEGORY and TEMP_KEY is None:
        TEMP_KEY = update.message.text
        BUTTON_REPLIES[TEMP_CATEGORY][TEMP_KEY] = {"text":"", "file":None}
        save_buttons()
        await update.message.reply_text("✅ تم إنشاء الزر الجديد. أرسل نص الزر:")
        return

    # إضافة محتوى للزر
    if TEMP_CATEGORY and TEMP_KEY:
        BUTTON_REPLIES[TEMP_CATEGORY][TEMP_KEY]["text"] = update.message.text
        save_buttons()
        await update.message.reply_text("✅ تم إضافة النص للزر. أرسل ملف PDF إذا أردت، أو /done للانتهاء.")
        return

    # إنهاء العملية
    if update.message.text == "/done":
        TEMP_CATEGORY = None
        TEMP_KEY = None
        TEMP_FILE = None
        await update.message.reply_text("✅ تم الانتهاء من العملية.")

# ========================== تشغيل البوت ==========================
async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))

    print("البوت يعمل الآن...")
    await app.run_polling()

# ========================== main ==========================
if __name__ == "__main__":
    asyncio.run(run_bot())
