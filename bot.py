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

# ========================== /start ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await register_user(update, context)
    await show_main_menu(update, context)

# ========================== تشغيل البوت ==========================
async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(handle_edit_category, pattern="^editcat_|editcatname|delcat$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_edit_category))
    app.add_handler(CallbackQueryHandler(manage_admins, pattern="manage_admins"))
    app.add_handler(CallbackQueryHandler(handle_admin_actions, pattern="add_admin|del_admin|deladmin_.*"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_admin))
    app.add_handler(CallbackQueryHandler(show_stats, pattern="stats"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))

    print("البوت يعمل الآن...")
    await app.run_polling()  # <-- طريقة التشغيل الصحيحة بدون مشاكل RuntimeWarning

# ========================== main ==========================
if __name__ == "__main__":
    asyncio.run(run_bot())
