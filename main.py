from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os

app = Flask(__name__)

with open("quiz.json", "r") as f:
    quiz = json.load(f)

user_states = {}

BOT_TOKEN = os.environ["BOT_TOKEN"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_states[update.effective_chat.id] = {"q": 0, "score": 0}
    await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = user_states[update.effective_chat.id]
    q_index = user["q"]

    if q_index >= len(quiz):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Quiz finished! Your score: {user['score']}/{len(quiz)}")
        return

    question = quiz[q_index]
    reply_markup = ReplyKeyboardMarkup([question["options"]], one_time_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=question["question"],
                                   reply_markup=reply_markup)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = user_states.get(update.effective_chat.id)
    if not user:
        return

    current_question = quiz[user["q"]]
    if update.message.text == current_question["answer"]:
        user["score"] += 1

    user["q"] += 1
    await send_question(update, context)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), ApplicationBuilder().token(BOT_TOKEN).build().bot)
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.process_update(update)
    return "OK"

if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    application.run_polling()
