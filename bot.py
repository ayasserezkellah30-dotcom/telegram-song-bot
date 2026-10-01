import os
import io
import requests
import threading
import asyncio

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN", "").strip()

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running!"


def run_flask():
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔎 البحث عن أغنية", callback_data="search")],
        [InlineKeyboardButton("ℹ️ طريقة الاستخدام", callback_data="help")],
    ]

    await update.message.reply_text(
        "🎵 أهلاً بك في بوت البحث عن الأغاني!\n\n"
        "اضغط على الزر بالأسفل ثم أرسل اسم الأغنية أو اسم الفنان.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "search":
        await query.message.reply_text(
            "🔎 أرسل الآن اسم الأغنية أو اسم الفنان.\n\n"
            "مثال:\n"
            "Matoub Lounes"
        )

    elif query.data == "help":
        await query.message.reply_text(
            "ℹ️ طريقة الاستخدام:\n\n"
            "1️⃣ اضغط «🔎 البحث عن أغنية»\n"
            "2️⃣ أرسل اسم الأغنية أو الفنان\n"
            "3️⃣ سأرسل لك مقطع Preview ورابط الاستماع الرسمي 🎵"
        )


async def search_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    if not query:
        return

    await update.message.reply_text("🔎 جاري البحث...")

    try:
        url = "https://itunes.apple.com/search"

        params = {
            "term": query,
            "media": "music",
            "entity": "song",
            "limit": 5,
        }

        response = requests.get(url, params=params, timeout=15)
        data = response.json()

        results = data.get("results", [])

        if not results:
            await update.message.reply_text(
                "❌ لم أجد نتائج.\n"
                "جرّب كتابة اسم الأغنية أو الفنان بطريقة مختلفة."
            )
            return

        for song in results:
            name = song.get("trackName", "غير معروف")
            artist = song.get("artistName", "غير معروف")
            album = song.get("collectionName", "غير معروف")
            link = song.get("trackViewUrl", "")
            preview_url = song.get("previewUrl", "")

            keyboard = []

            if link:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            "🎧 الاستماع للأغنية كاملة",
                            url=link
                        )
                    ]
                )

            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

            caption = (
                f"🎵 {name}\n"
                f"👤 الفنان: {artist}\n"
                f"💿 الألبوم: {album}\n\n"
            )

            if preview_url:
                try:
                    audio_response = requests.get(
                        preview_url,
                        timeout=20
                    )
                    audio_response.raise_for_status()

                    audio_file = io.BytesIO(audio_response.content)
                    audio_file.name = f"{name}.m4a"

                    await update.message.reply_audio(
                        audio=audio_file,
                        title=name,
                        performer=artist,
                        caption=caption + "ℹ️ هذا مقطع Preview قصير من iTunes.",
                        reply_markup=reply_markup,
                    )

                except Exception:
                    await update.message.reply_text(
                        caption + "ℹ️ المقطع الصوتي غير متاح حاليًا.",
                        reply_markup=reply_markup,
                    )

            else:
                await update.message.reply_text(
                    caption + "ℹ️ لا يوجد Preview متاح لهذه الأغنية.",
                    reply_markup=reply_markup,
                )

    except Exception as e:
        print("ERROR:", e)

        await update.message.reply_text(
            "⚠️ حدث خطأ أثناء البحث.\n"
            "حاول مرة أخرى بعد قليل."
        )


async def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search_song
        )
    )

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    await asyncio.Event().wait()


if __name__ == "__main__":
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    asyncio.run(main())
