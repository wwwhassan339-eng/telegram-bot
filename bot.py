from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import os
import json

BOT_TOKEN = "8495189316:AAGAzS9MTMfal703P-ncF7xMedg2RxqMBbo"  # ضع توكن البوت هنا
MAIN_ADMIN_ID = 643482335  # أدمن رئيسي

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

# ==========================
def has_permission(user_id, perm):
    return str(user_id) in ADMINS and perm in ADMINS[str(user_id)]["permissions"]

# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

async def show_main_menu(update, context, message=None):
    keyboard = []
    row = []

    for category in BUTTON_REPLIES.keys():
        row.append(InlineKeyboardButton(category, callback_data=f"cat_{category}"))
        if len(row)==2:
            keyboard.append(row)
            row=[]
    if row:
        keyboard.append(row)

    if str(update.effective_user.id) in ADMINS:
        admin_row = [
            InlineKeyboardButton("➕ إضافة فئة جديدة", callback_data="add_category"),
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
    global TEMP_CATEGORY, TEMP_KEY, TEMP_FILE, EDIT_CATEGORY, EDIT_KEY, EDIT_OPTION
    global TEMP_ADMIN_ID, TEMP_ADMIN_PERMS
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
        # إشعار للأدمن الرئيسي
        await context.bot.send_message(
            chat_id=MAIN_ADMIN_ID,
            text=f"🆕 مستخدم جديد دخل البوت:\nID: {user_id}\nيوزر: @{query.from_user.username}\nالاسم: {query.from_user.first_name} {query.from_user.last_name or ''}"
        )

    # --------------------
    # الأدمنين
    if str(user_id) in ADMINS:
        # إضافة فئة
        if data=="add_category" and has_permission(user_id,"add"):
            TEMP_CATEGORY = None
            await query.message.reply_text("✏️ أرسل اسم الفئة الجديدة:")
            return
        # تعديل فئة
        elif data=="edit_category" and has_permission(user_id,"edit"):
            keyboard=[[InlineKeyboardButton(cat,callback_data=f"editcat_{cat}")] for cat in BUTTON_REPLIES.keys()]
            keyboard.append([InlineKeyboardButton("🔙 رجوع",callback_data="back")])
            await query.message.reply_text("اختر الفئة لتعديلها:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        # حذف فئة
        elif data=="delete_category" and has_permission(user_id,"delete"):
            keyboard=[[InlineKeyboardButton(cat,callback_data=f"delcat_{cat}")] for cat in BUTTON_REPLIES.keys()]
            keyboard.append([InlineKeyboardButton("🔙 رجوع",callback_data="back")])
            await query.message.reply_text("اختر الفئة للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        # الإحصائيات
        elif data=="stats" and has_permission(user_id,"stats"):
            num_users=len(USERS)
            num_categories=len(BUTTON_REPLIES)
            total_buttons=sum(len(v) for v in BUTTON_REPLIES.values())
            usernames=[f"@{v['username']}" for v in USERS.values() if v['username']]
            stats_text=f"📊 إحصائيات البوت:\nعدد المستخدمين:{num_users}\nعدد الفئات:{num_categories}\nعدد الأزرار:{total_buttons}\nالمستخدمون:\n"+"\n".join(usernames)
            await query.message.reply_text(stats_text)
            return
        # إدارة الأدمن
        elif data=="manage_admins" and has_permission(user_id,"manage_admins"):
            keyboard=[
                [InlineKeyboardButton("➕ إضافة أدمن", callback_data="add_new_admin")],
                [InlineKeyboardButton("❌ حذف أدمن", callback_data="del_admin")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ]
            await query.message.reply_text("👑 إدارة الأدمن: اختر العملية:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data=="add_new_admin":
            await query.message.reply_text("✏️ أرسل رقم الـ ID للأدمن الجديد:")
            TEMP_ADMIN_ID = None
            TEMP_ADMIN_PERMS=[]
            return
        elif data=="del_admin":
            keyboard=[[InlineKeyboardButton(k,callback_data=f"deladmin_{k}")] for k in ADMINS.keys() if k!=str(MAIN_ADMIN_ID)]
            keyboard.append([InlineKeyboardButton("🔙 رجوع",callback_data="back")])
            await query.message.reply_text("اختر الأدمن للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data.startswith("deladmin_"):
            del_id=data.replace("deladmin_","")
            if del_id in ADMINS:
                ADMINS.pop(del_id)
                save_admins()
                await query.message.reply_text(f"✅ تم حذف الأدمن {del_id}")
            return

    # --------------------
    # الطلاب والفئات
    if data.startswith("cat_"):
        category=data.replace("cat_","")
        keyboard=[[InlineKeyboardButton(k,callback_data=f"userbtn_{category}_{k}")] for k in BUTTON_REPLIES.get(category,{}).keys()]
        keyboard.append([InlineKeyboardButton("🔙 رجوع",callback_data="back")])
        await query.message.edit_text(f"📂 فئة: {category}", reply_markup=InlineKeyboardMarkup(keyboard))
        return
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
    # زر رجوع
    if data=="back":
        await show_main_menu(update, context)
        return

# ==========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TEMP_CATEGORY, TEMP_KEY, TEMP_FILE, EDIT_CATEGORY, EDIT_KEY, EDIT_OPTION, TEMP_ADMIN_ID, TEMP_ADMIN_PERMS
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
        await update.message.reply_text("✅ تم حفظ الملف، أرسل النص ليكمل الزر أو الفئة.")
        return

    # إضافة فئة جديدة
    if TEMP_CATEGORY is None:
        TEMP_CATEGORY=update.message.text
        if TEMP_CATEGORY not in BUTTON_REPLIES:
            BUTTON_REPLIES[TEMP_CATEGORY]={}
            save_buttons()
            await update.message.reply_text(f"✅ تم إنشاء الفئة '{TEMP_CATEGORY}' بنجاح! الآن أرسل /start لإضافة أزرار داخلها.")
        TEMP_CATEGORY=None
        return

    # إضافة أدمن جديد
    if TEMP_ADMIN_ID is None and update.message.text.isdigit():
        TEMP_ADMIN_ID=str(update.message.text)
        perms_keyboard=[
            [InlineKeyboardButton("➕ إضافة أزرار",callback_data="perm_add"),
             InlineKeyboardButton("📝 تعديل أزرار",callback_data="perm_edit")],
            [InlineKeyboardButton("❌ حذف أزرار",callback_data="perm_delete"),
             InlineKeyboardButton("📊 إحصائيات",callback_data="perm_stats")],
            [InlineKeyboardButton("👑 إدارة أدمن",callback_data="perm_admins")],
            [InlineKeyboardButton("✅ إنهاء",callback_data="perm_done")]
        ]
        await update.message.reply_text("اختر صلاحيات الأدمن الجديد (اضغط على كل زر لتحديده ثم إنهاء):", reply_markup=InlineKeyboardMarkup(perms_keyboard))
        return

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
