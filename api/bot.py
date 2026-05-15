import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

telegram_app = Application.builder().token(TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yo 👋 Bot is alive on Vercel")


telegram_app.add_handler(CommandHandler("start", start))


@app.route("/", methods=["GET", "POST"])
async def webhook():
    if request.method == "GET":
        return "Telegram bot running"
    
    data = request.get_json()
    update = Update.de_json(data, telegram_app.bot)

    await telegram_app.initialize()
    await telegram_app.process_update(update)

    return "ok"