import os
import requests
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

@app.get("/")
def home():
    return "Bot is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 مرحباً بك!\n\n"
        "أرسل اسم الأغنية أو اسم الفنان وسأبحث لك عنها 🔎"
    )

async def search_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    if not query:
        return

    await update.message.reply_text("🔎 جاري البحث...")

    try:
        response = requests.get(
            "https://itunes.apple.com/search",
            params={
                "term": query,
                "media": "music",
                "entity": "song",
                "limit": 5
            },
            timeout=10
        )

        data = response.json()
        results = data.get("results", [])

        if not results:
            await update.message.reply_text("❌ لم أجد أغنية بهذا الاسم.")
            return

        message = "🎵 نتائج البحث:\n\n"

        for song in results:
            name = song.get("trackName", "غير معروف")
            artist = song.get("artistName", "غير معروف")
            album = song.get("collectionName", "غير معروف")
            link = song.get("trackViewUrl", "")

            message += (
                f"🎶 {name}\n"
                f"👤 الفنان: {artist}\n"
                f"💿 الألبوم: {album}\n"
                f"🔗 {link}\n\n"
            )

        await update.message.reply_text(message)

    except Exception:
        await update.message.reply_text(
            "⚠️ حدث خطأ أثناء البحث، حاول مرة أخرى."
        )

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def main():
    threading.Thread(target=run_web, daemon=True).start()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search_song)
    )

    application.run_polling()

if __name__ == "__main__":
    main()
