import json
import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
import requests

# إعدادات
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get('PORT', 8443))
USER_DATA_FILE = "data.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
scheduler.start()

def load_user_data():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, "r") as f:
        return json.load(f)

def save_user_data(user_id, phone, notify=False):
    data = load_user_data()
    data[str(user_id)] = {"phone": phone, "notify": notify}
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

def get_balance(phone):
    try:
        url = f"http://portal.yemen.net.ye/?service=balance&phone={phone}"
        response = requests.get(url)
        if response.status_code == 200:
            return f"📶 رصيد الباقة: {response.text.strip()}"
        else:
            return "❌ لم يتم التمكن من جلب الرصيد حالياً."
    except Exception as e:
        return f"⚠️ خطأ أثناء جلب الرصيد: {e}"

def check_balance_job(context):
    data = load_user_data()
    for user_id, info in data.items():
        if info.get("notify"):
            phone = info.get("phone")
            balance = get_balance(phone)
            context.bot.send_message(chat_id=int(user_id), text=f"{balance}

مع تحيات المهندس نجيب الخالدي
📱 772882439")

def send_balance_now(context, user_id):
    data = load_user_data()
    phone = data.get(str(user_id), {}).get("phone")
    if phone:
        balance = get_balance(phone)
        context.bot.send_message(chat_id=user_id, text=f"{balance}

مع تحيات المهندس نجيب الخالدي
📱 772882439")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أرسل رقم الهاتف الثابت (يمن نت) للاستعلام عن رصيدك.
"
        "مثال: 01xxxxxx
"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text.startswith("01") and len(text) >= 7:
        reply_keyboard = [["نعم", "لا"]]
        context.user_data["pending_phone"] = text
        await update.message.reply_text(
            f"هل تريد حفظ الرقم {text}؟",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
    elif text == "نعم" and "pending_phone" in context.user_data:
        phone = context.user_data.pop("pending_phone")
        save_user_data(user_id, phone, notify=True)
        scheduler.add_job(check_balance_job, 'interval', minutes=10, args=[context])
        send_balance_now(context, user_id)
        await update.message.reply_text("✅ تم تفعيل الإشعارات كل 10 دقائق.")
    elif text == "لا":
        await update.message.reply_text("❌ تم إلغاء العملية.")
    else:
        await update.message.reply_text("⚠️ الرجاء إرسال رقم يبدأ بـ 01")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
