from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import os, json

BOT_TOKEN = "8495189316:AAGAzS9MTMfal703P-ncF7xMedg2RxqMBbo"
MAIN_ADMIN_ID = 643482335

DATA_FILE = "buttons.json"
USERS_FILE = "users.json"
ADMINS_FILE = "admins.json"

# ==========================
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

if os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "r", encoding="utf-8") as f:
        ADMINS = json.load(f)
else:
    ADMINS = {str(MAIN_ADMIN_ID): {"permissions":["add","edit","delete","stats","manage_admins"]}}

# ==========================
# متغيرات مؤقتة لإدارة العمليات
TEMP_CATEGORY = None
TEMP_KEY = None
TEMP_FILE = None
EDIT_CATEGORY = None
EDIT_KEY = None
EDIT_OPTION = None
TEMP_ADMIN_ID = None
TEMP_ADMIN_PERMS = []

# ==========================
def save_buttons():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(BUTTON_REPLIES, f, ensure_ascii=False, indent=2)

def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(USERS, f, ensure_ascii=False, indent=2)

def save_admins():
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(ADMINS, f, ensure_ascii=False, indent=2)

def has_permission(user_id, perm):
    return str(user_id) in ADMINS and perm in ADMINS[str(user_id)]["permissions"]

def split_button_text(text, max_len=20):
    """تقسيم النص الطويل للزر إلى سطرين إذا لزم"""
    if len(text) <= max_len:
        return text
    idx = text.rfind(" ",0,max_len)
    if idx==-1:
        idx = max_len
    return text[:idx] + "\n" + text[idx:].strip()

# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

async def show_main_menu(update, context, message=None):
    keyboard = []
    row = []

    for category in BUTTON_REPLIES.keys():
        row.append(InlineKeyboardButton(split_button_text(category), callback_data=f"cat_{category}"))
        if len(row)==2:
            keyboard.append(row)
            row=[]
    if row:
        keyboard.append(row)

    if str(update.effective_user.id) in ADMINS:
        admin_row = [
            InlineKeyboardButton("➕ إضافة فئة", callback_data="add_category"),
            InlineKeyboardButton("📝 تعديل فئة/زر", callback_data="edit_category"),
            InlineKeyboardButton("❌ حذف فئة/زر", callback_data="delete_category"),
            InlineKeyboardButton("📊 إحصائيات البوت", callback_data="stats"),
            InlineKeyboardButton("👑 إدارة الأدمن", callback_data="manage_admins")
        ]
        keyboard.append(admin_row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "👋 أهلاً! اختر فئة 👇" if str(update.effective_user.id) not in ADMINS else "👑 واجهة الأدمن: اختر فئة أو إدارة"
    if message:
        await message.edit_text(text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

# ==========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TEMP_CATEGORY, TEMP_KEY, TEMP_FILE
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
            chat_id=MAIN_ADMIN_ID,
            text=f"🆕 مستخدم جديد دخل البوت:\nID: {user_id}\nيوزر: @{query.from_user.username}\nالاسم: {query.from_user.first_name} {query.from_user.last_name or ''}"
        )

    # --------------------
    # واجهة فئات الطلاب + الأدمن
    if data.startswith("cat_"):
        category=data.replace("cat_","")
        keyboard=[]
        # أزرار الطلاب
        for k in BUTTON_REPLIES.get(category,{}).keys():
            keyboard.append([InlineKeyboardButton(split_button_text(k), callback_data=f"userbtn_{category}_{k}")])
        # أزرار إدارة للأدمن داخل الفئة
        if str(user_id) in ADMINS:
            admin_row = [
                InlineKeyboardButton("➕ إضافة زر", callback_data=f"addbtn_{category}"),
                InlineKeyboardButton("📝 تعديل زر", callback_data=f"editbtn_{category}"),
                InlineKeyboardButton("❌ حذف زر", callback_data=f"delbtn_{category}"),
                InlineKeyboardButton("🗂 إضافة محتوى للزر", callback_data=f"addcontent_{category}")
            ]
            keyboard.append(admin_row)
        keyboard.append([InlineKeyboardButton("🔙 رجوع",callback_data="back")])
        await query.message.edit_text(f"📂 فئة: {category}", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # زر اختيار الطلاب للزر
    if data.startswith("userbtn_"):
        parts=data.replace("userbtn_","").split("_",1)
        category=parts[0]
        key=parts[1]
        info=BUTTON_REPLIES.get(category,{}).get(key,{})
        if info.get("file"):
            file_path=info["file"]
            file_name=os.path.basename(file_path)
            await query.message.reply_document(InputFile(file_path, filename=file_name), caption=info.get("text",""))
        else:
            await query.message.edit_text(info.get("text",""))
        return

    # أزرار إدارة الأدمن داخل الفئة
    if str(user_id) in ADMINS:
        # إضافة زر جديد
        if data.startswith("addbtn_"):
            TEMP_CATEGORY = data.replace("addbtn_","")
            TEMP_KEY = None
            await query.message.reply_text(f"✏️ أرسل اسم الزر الجديد في فئة {TEMP_CATEGORY}:")
            return
        # تعديل زر
        if data.startswith("editbtn_"):
            EDIT_CATEGORY = data.replace("editbtn_","")
            keyboard=[[InlineKeyboardButton(split_button_text(k), callback_data=f"editbtnkey_{EDIT_CATEGORY}_{k}")] 
                      for k in BUTTON_REPLIES.get(EDIT_CATEGORY,{})]
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
            await query.message.reply_text("اختر الزر لتعديله:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        # حذف زر
        if data.startswith("delbtn_"):
            EDIT_CATEGORY = data.replace("delbtn_","")
            keyboard=[[InlineKeyboardButton(split_button_text(k), callback_data=f"delbtnkey_{EDIT_CATEGORY}_{k}")] 
                      for k in BUTTON_REPLIES.get(EDIT_CATEGORY,{})]
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
            await query.message.reply_text("اختر الزر للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        # إضافة محتوى للزر موجود
        if data.startswith("addcontent_"):
            TEMP_CATEGORY = data.replace("addcontent_","")
            TEMP_KEY = None
            await query.message.reply_text(f"✏️ أرسل اسم الزر لإضافة محتوى له في فئة {TEMP_CATEGORY}:")
            return

    # زر رجوع
    if data=="back":
        await show_main_menu(update, context)
        return

# ==========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TEMP_CATEGORY, TEMP_KEY, TEMP_FILE
    user_id=update.effective_user.id
    if str(user_id) not in ADMINS:
        return

    # استقبال ملف PDF
    if update.message.document:
        TEMP_FILE=await update.message.document.get_file()
        os.makedirs("files",exist_ok=True)
        file_path=f"files/{update.message.document.file_name}"
        await TEMP_FILE.download_to_drive(file_path)
        TEMP_FILE=file_path
        if TEMP_CATEGORY and TEMP_KEY:
            BUTTON_REPLIES[TEMP_CATEGORY][TEMP_KEY]["file"] = TEMP_FILE
            save_buttons()
        await update.message.reply_text("✅ تم رفع الملف بنجاح.")
        return

    # إضافة زر جديد
    if TEMP_CATEGORY and TEMP_KEY is None:
        TEMP_KEY = update.message.text
        BUTTON_REPLIES[TEMP_CATEGORY][TEMP_KEY] = {"text":"","file":None}
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
    if update.message.text=="/done":
        TEMP_CATEGORY = None
        TEMP_KEY = None
        TEMP_FILE = None
        await update.message.reply_text("✅ تم الانتهاء من العملية.")

# ==========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))
    print("البوت يعمل الآن...")
    app.run_polling()

if __name__=="__main__":
    main()
