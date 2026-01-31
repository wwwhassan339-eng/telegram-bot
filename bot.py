from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import os, json, asyncio

BOT_TOKEN = "8495189316:AAGAzS9MTMfal703P-ncF7xMedg2RxqMBbo"  # ضع توكن جديد هنا
MAIN_ADMIN_ID = 643482335  # أدمن رئيسي

DATA_FILE = "buttons.json"
USERS_FILE = "users.json"
ADMINS_FILE = "admins.json"

# ==========================
# تحميل البيانات أو تهيئتها إذا غير موجودة
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

BUTTON_REPLIES = load_json(DATA_FILE, {})
USERS = load_json(USERS_FILE, {})
ADMINS = load_json(ADMINS_FILE, {str(MAIN_ADMIN_ID): {"permissions":["add","edit","delete","stats","manage_admins"]}})

# ==========================
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

# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

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

    # أزرار إدارة الأدمن
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

# ==========================
# إشعار الأدمن عند دخول مستخدم جديد
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

# ==========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    await register_user(update, context)  # تسجيل المستخدم إذا جديد

    # ----------------- اختيار فئة -----------------
    if data.startswith("cat_"):
        category = data.replace("cat_", "")
        keyboard = [[InlineKeyboardButton(split_button_text(k), callback_data=f"userbtn_{category}_{k}")] 
                    for k in BUTTON_REPLIES.get(category, {})]
        # أزرار إدارة الأدمن داخل الفئة
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

    # ----------------- اختيار زر المستخدم -----------------
    if data.startswith("userbtn_"):
        parts = data.replace("userbtn_", "").split("_", 1)
        category, key = parts[0], parts[1]
        info = BUTTON_REPLIES.get(category, {}).get(key, {})
        if info.get("file"):
            file_path = info["file"]
            file_name = os.path.basename(file_path)
            try:
                await query.message.reply_document(InputFile(file_path, filename=file_name), caption=info.get("text", ""))
            except:
                await query.message.reply_text(info.get("text", ""))
        else:
            await query.message.edit_text(info.get("text", ""))
        return

    # ----------------- إدارة الأدمن: إضافة زر / محتوى -----------------
    if str(user_id) in ADMINS:
        if data.startswith("addbtn_"):
            category = data.replace("addbtn_", "")
            context.user_data["temp_category"] = category
            context.user_data["temp_key"] = None
            await query.message.reply_text(f"✏️ أرسل اسم الزر الجديد في فئة {category}:")
            return
        if data.startswith("addcontent_"):
            category = data.replace("addcontent_", "")
            context.user_data["temp_category"] = category
            context.user_data["temp_key"] = None
            await query.message.reply_text(f"✏️ أرسل اسم الزر لإضافة محتوى له في فئة {category}:")
            return

    # ----------------- تعديل/حذف فئة/زر -----------------
    if data == "edit_category":
        await admin_edit_category(update, context)
        return
    if data == "manage_admins":
        await manage_admins(update, context)
        return
    if data == "stats":
        await show_stats(update, context)
        return
    if data == "back":
        await show_main_menu(update, context)
        return

# ----------------- التعامل مع رسائل النصوص / الملفات -----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) not in ADMINS: return

    temp_category = context.user_data.get("temp_category")
    temp_key = context.user_data.get("temp_key")

    # استقبال ملف PDF
    if update.message.document:
        file = await update.message.document.get_file()
        os.makedirs("files", exist_ok=True)
        file_path = f"files/{update.message.document.file_name}"
        try:
            await file.download_to_drive(file_path)
        except:
            await update.message.reply_text("❌ حدث خطأ أثناء رفع الملف.")
            return
        if temp_category and temp_key:
            BUTTON_REPLIES[temp_category][temp_key]["file"] = file_path
            save_buttons()
        await update.message.reply_text("✅ تم رفع الملف بنجاح.")
        return

    # إضافة زر جديد
    if temp_category and temp_key is None:
        temp_key = update.message.text
        context.user_data["temp_key"] = temp_key
        BUTTON_REPLIES[temp_category][temp_key] = {"text": "", "file": None}
        save_buttons()
        await update.message.reply_text("✅ تم إنشاء الزر الجديد. أرسل نص الزر:")
        return

    # إضافة محتوى للزر
    if temp_category and temp_key:
        BUTTON_REPLIES[temp_category][temp_key]["text"] = update.message.text
        save_buttons()
        await update.message.reply_text("✅ تم إضافة النص للزر. أرسل ملف PDF إذا أردت، أو /done للانتهاء.")
        return

    # إنهاء العملية
    if update.message.text == "/done":
        context.user_data.clear()
        await update.message.reply_text("✅ تم الانتهاء من العملية.")

# ==========================
# إدارة الفئات عبر واجهة رسومية
async def admin_edit_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(split_button_text(cat), callback_data=f"editcat_{cat}")]
                for cat in BUTTON_REPLIES.keys()]
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
    await query.message.edit_text("اختر الفئة لتعديلها:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_edit_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("editcat_"):
        category = data.replace("editcat_", "")
        context.user_data["edit_category"] = category
        keyboard = [
            [InlineKeyboardButton("📝 تعديل اسم الفئة", callback_data="editcatname")],
            [InlineKeyboardButton("❌ حذف الفئة كاملة", callback_data="delcat")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
        ]
        await query.message.edit_text(f"فئة: {category}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "editcatname":
        await query.message.reply_text("✏️ أرسل الاسم الجديد للفئة:")
        context.user_data["awaiting_cat_name"] = True

    elif data == "delcat":
        cat = context.user_data.get("edit_category")
        if cat and cat in BUTTON_REPLIES:
            del BUTTON_REPLIES[cat]
            save_buttons()
            await query.message.reply_text(f"✅ تم حذف الفئة {cat}")
        await show_main_menu(update, context)

async def handle_message_edit_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_cat_name"):
        old_name = context.user_data.get("edit_category")
        new_name = update.message.text.strip()
        if old_name in BUTTON_REPLIES:
            BUTTON_REPLIES[new_name] = BUTTON_REPLIES.pop(old_name)
            save_buttons()
            await update.message.reply_text(f"✅ تم تعديل اسم الفئة إلى {new_name}")
        context.user_data.pop("awaiting_cat_name", None)
        context.user_data.pop("edit_category", None)
        await show_main_menu(update, context)

# ==========================
# إدارة الأدمنز
async def manage_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("➕ إضافة أدمن جديد", callback_data="add_admin")],
        [InlineKeyboardButton("❌ حذف أدمن", callback_data="del_admin")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
    ]
    await query.message.edit_text("👑 إدارة الأدمن:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "add_admin":
        await query.message.reply_text("✏️ أرسل ID الأدمن الجديد:")
        context.user_data["awaiting_new_admin"] = True
    elif data == "del_admin":
        keyboard = [[InlineKeyboardButton(f"{aid}", callback_data=f"deladmin_{aid}")]
                    for aid in ADMINS.keys() if int(aid) != MAIN_ADMIN_ID]
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
        await query.message.edit_text("اختر الأدمن للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("deladmin_"):
        aid = data.replace("deladmin_", "")
        if aid in ADMINS:
            del ADMINS[aid]
            save_admins()
            await query.message.reply_text(f"✅ تم حذف الأدمن {aid}")
        await show_main_menu(update, context)

async def handle_message_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_new_admin"):
        new_admin_id = update.message.text.strip()
        if new_admin_id not in ADMINS:
            ADMINS[new_admin_id] = {"permissions":["add","edit","delete","stats","manage_admins"]}
            save_admins()
            await update.message.reply_text(f"✅ تم إضافة الأدمن {new_admin_id} مع صلاحيات كاملة")
        else:
            await update.message.reply_text("❌ هذا المستخدم موجود بالفعل كأدمن")
        context.user_data.pop("awaiting_new_admin", None)
        await show_main_menu(update, context)

# ==========================
# إحصائيات البوت
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    num_users = len(USERS)
    num_categories = len(BUTTON_REPLIES)
    num_buttons = sum(len(BUTTON_REPLIES[cat]) for cat in BUTTON_REPLIES)
    num_files = sum(1 for cat in BUTTON_REPLIES for btn in BUTTON_REPLIES[cat] if BUTTON_REPLIES[cat][btn].get("file"))

    text = (
        f"📊 إحصائيات البوت:\n\n"
        f"👥 عدد المستخدمين: {num_users}\n"
        f"🗂 عدد الفئات: {num_categories}\n"
        f"🔘 عدد الأزرار: {num_buttons}\n"
        f"📄 عدد الملفات المرفوعة: {num_files}"
    )

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================
# تشغيل البوت
async def run_bot():
    while True:
        try:
            app = ApplicationBuilder().token(BOT_TOKEN).build()

            # أوامر
            app.add_handler(CommandHandler("start", start))

            # التعامل مع الأزرار
            app.add_handler(CallbackQueryHandler(button_handler))

            # تعديل الفئات
            app.add_handler(CallbackQueryHandler(handle_edit_category, pattern="^editcat_|editcatname|delcat$"))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_edit_category))

            # إدارة الأدمنز
            app.add_handler(CallbackQueryHandler(manage_admins, pattern="manage_admins"))
            app.add_handler(CallbackQueryHandler(handle_admin_actions, pattern="add_admin|del_admin|deladmin_.*"))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_admin))

            # الإحصائيات
            app.add_handler(CallbackQueryHandler(show_stats, pattern="stats"))

            # رسائل المستخدمين والأزرار
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            app.add_handler(MessageHandler(filters.Document.ALL, handle_message))

            print("البوت يعمل الآن...")
            await app.run_polling()
        except Exception as e:
            print(f"❌ خطأ في الاتصال، إعادة المحاولة تلقائيًا: {e}")
            await asyncio.sleep(5)

# ==========================
if __name__ == "__main__":
    asyncio.run(run_bot())
