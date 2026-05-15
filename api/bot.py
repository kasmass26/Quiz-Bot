import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

telegram_app = Application.builder().token(TOKEN).build()

# Quiz data
QUIZ = [
    {
        "question": "What is the capital of France?",
        "options": {"A": "Paris", "B": "Lyon", "C": "Marseille", "D": "Nice"},
        "correct": "A",
        "explanation": "Paris is the capital and largest city of France."
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "options": {"A": "Venus", "B": "Mars", "C": "Jupiter", "D": "Saturn"},
        "correct": "B",
        "explanation": "Mars is called the Red Planet due to its reddish appearance caused by iron oxide on its surface."
    },
    {
        "question": "What is the largest ocean on Earth?",
        "options": {"A": "Atlantic", "B": "Indian", "C": "Arctic", "D": "Pacific"},
        "correct": "D",
        "explanation": "The Pacific Ocean is the largest and deepest ocean on Earth."
    },
    {
        "question": "Who wrote 'Romeo and Juliet'?",
        "options": {"A": "Jane Austen", "B": "William Shakespeare", "C": "Mark Twain", "D": "Charles Dickens"},
        "correct": "B",
        "explanation": "William Shakespeare wrote 'Romeo and Juliet', one of the most famous love stories in literature."
    },
    {
        "question": "What is the smallest prime number?",
        "options": {"A": "0", "B": "1", "C": "2", "D": "3"},
        "correct": "C",
        "explanation": "2 is the smallest prime number and the only even prime number."
    }
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yo 👋 Bot is alive on Vercel\n\nType /quiz to start the quiz!")


async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quiz_index"] = 0
    context.user_data["score"] = 0
    await send_question(update, context)


async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quiz_index = context.user_data["quiz_index"]
    
    if quiz_index >= len(QUIZ):
        # Quiz finished
        score = context.user_data["score"]
        await update.callback_query.edit_message_text(
            f"🎉 Quiz Complete!\n\nYour Score: {score}/{len(QUIZ)}\n\nType /quiz to try again!"
        ) if update.callback_query else await update.message.reply_text(
            f"🎉 Quiz Complete!\n\nYour Score: {score}/{len(QUIZ)}\n\nType /quiz to try again!"
        )
        return
    
    question_data = QUIZ[quiz_index]
    question_text = f"Question {quiz_index + 1}/{len(QUIZ)}\n\n{question_data['question']}"
    
    # Create inline keyboard with options
    buttons = [
        [InlineKeyboardButton(f"A: {question_data['options']['A']}", callback_data=f"answer_A_{quiz_index}"),
         InlineKeyboardButton(f"B: {question_data['options']['B']}", callback_data=f"answer_B_{quiz_index}")],
        [InlineKeyboardButton(f"C: {question_data['options']['C']}", callback_data=f"answer_C_{quiz_index}"),
         InlineKeyboardButton(f"D: {question_data['options']['D']}", callback_data=f"answer_D_{quiz_index}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(question_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(question_text, reply_markup=reply_markup)


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    answer_choice = data.split("_")[1]
    quiz_index = int(data.split("_")[2])
    
    question_data = QUIZ[quiz_index]
    is_correct = answer_choice == question_data["correct"]
    
    if is_correct:
        context.user_data["score"] += 1
        result = "✅ Correct!"
    else:
        result = f"❌ Wrong! Correct answer: {question_data['correct']}"
    
    explanation = f"\n\n📚 {question_data['explanation']}"
    message = f"{result}{explanation}\n\nScore: {context.user_data['score']}/{len(QUIZ)}"
    
    context.user_data["quiz_index"] += 1
    
    # Show next question or end quiz
    buttons = [[InlineKeyboardButton("Next Question ➡️", callback_data="next_question")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(message, reply_markup=reply_markup)


async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_question(update, context)


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("quiz", quiz_start))
telegram_app.add_handler(CallbackQueryHandler(handle_answer, pattern=r"answer_"))
telegram_app.add_handler(CallbackQueryHandler(next_question, pattern=r"next_question"))


@app.route("/", methods=["GET", "POST"])
async def webhook():
    if request.method == "GET":
        return "Telegram bot running"
    
    data = request.get_json()
    update = Update.de_json(data, telegram_app.bot)

    await telegram_app.initialize()
    await telegram_app.process_update(update)

    return "ok"