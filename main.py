import os
import json
import requests
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

BOT_TOKEN = "8463429711:AAFbgxTZ9Nr1rhMlCtvj6igFOdJvt-uuoZ4"
DATA_FILE = "data.json"


# 🔹 تحميل البيانات
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# 🔹 حفظ البيانات
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 🔹 استعلام الرصيد
def query_balance(phone_number: str):
    url = "https://adsl-yemen.com/"
    data = {"mobile": phone_number, "action": "query"}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.post(url, data=data, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        boxes = soup.find_all("div", class_="result-box")
        if not boxes:
            return None

        info = {}
        for b in boxes:
            title = b.find("div", class_="result-title")
            value = b.find("div", class_="result-value")
            if title and value:
                info[title.text.strip()] = value.text.strip()

        return info
    except Exception as e:
        print(f"⚠️ Error in query_balance: {e}")
        return None


# 🔹 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    phones = data.get(user_id, {}).get("phones", [])

    keyboard = [[p] for p in phones]
    keyboard.append(["استعلام الكل"] if phones else ["استعلام رصيد"])

    await update.message.reply_text(
        "مرحبًا بك! 👋\nأرسل رقم الهاتف الأرضي (مثال: 01XXXXXX) أو اختر من الأرقام المحفوظة:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# 🔹 التعامل مع الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    data = load_data()
    phones = data.get(user_id, {}).get("phones", [])

    # استعلام الكل
    if text == "استعلام الكل":
        if not phones:
            await update.message.reply_text("⚠️ لا توجد أرقام محفوظة لديك.")
            return

        await update.message.reply_text("🔄 جاري الاستعلام عن جميع الأرقام المحفوظة ...")
        for number in phones:
            await update.message.reply_text(f"📞 الرقم: {number}\n🔍 جاري الاستعلام...")
            info = query_balance(number)
            if not info:
                await update.message.reply_text(f"❌ فشل الاستعلام عن {number}.")
                continue

            msg = (
                f"📞 *الرقم:* {number}\n"
                f"📡 *الرصيد الحالي:* {info.get('الرصيد الحالي', '?')}\n"
                f"💳 *قيمة الباقة:* {info.get('قيمة الباقة', '?')} ريال\n"
                f"📅 *تاريخ الانتهاء:* {info.get('تاريخ الانتهاء', '?')}\n\n"
                f"مع تحيات المهندس نجيب أحمد الخالدي 📞 772882439"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        return

    # استعلام رصيد جديد
    if text == "استعلام رصيد":
        await update.message.reply_text("📝 أرسل رقم الهاتف الأرضي (مثال: 01XXXXXXX).")
        return

    # حفظ الرقم (نعم/لا)
    if text in ("نعم", "لا"):
        last_number = context.user_data.get("last_number")
        if text == "نعم" and last_number:
            if last_number not in phones:
                phones.append(last_number)
            data[user_id] = {"phones": phones}
            save_data(data)
            await update.message.reply_text("✅ تم حفظ الرقم.")

        keyboard = [[p] for p in phones]
        keyboard.append(["استعلام الكل"] if phones else ["استعلام رصيد"])
        await update.message.reply_text(
            "اختر رقمًا محفوظًا أو أرسل رقمًا جديدًا:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    # تحقق من صحة الرقم
    if not text.startswith("0") or len(text) != 8 or not text.isdigit():
        await update.message.reply_text("⚠️ أدخل رقمًا صحيحًا (مثال: 01694455).")
        return

    # استعلام فردي
    await update.message.reply_text("🔍 جاري الاستعلام عن الرصيد ...")
    info = query_balance(text)
    if not info:
        await update.message.reply_text("❌ لم أستطع جلب البيانات، أعد المحاولة لاحقًا.")
        return

    msg = (
        f"📡 *الرصيد الحالي:* {info.get('الرصيد الحالي', '?')}\n"
        f"💳 *قيمة الباقة:* {info.get('قيمة الباقة', '?')} ريال\n"
        f"📅 *تاريخ الانتهاء:* {info.get('تاريخ الانتهاء', '?')}\n\n"
        f"مع تحيات المهندس نجيب أحمد الخالدي 📞 772882439"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

    if text not in phones:
        context.user_data["last_number"] = text
        await update.message.reply_text(
            "هل تريد حفظ الرقم؟",
            reply_markup=ReplyKeyboardMarkup([["نعم", "لا"]], resize_keyboard=True)
        )
    else:
        keyboard = [[p] for p in phones]
        keyboard.append(["استعلام الكل"] if phones else ["استعلام رصيد"])
        await update.message.reply_text(
            "اختر رقمًا محفوظًا أو أرسل رقمًا جديدًا:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )


# 🔹 تشغيل البوت
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()
