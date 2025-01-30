import os
from typing import Final
from pymongo import MongoClient
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import google.generativeai as genai
import datetime
import requests
from dotenv import load_dotenv

load_dotenv(".env.local")

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['Telegram']
users_collection = db['Task']
chat_history_collection = db['ChatHistory']
file_analysis_collection = db['FileAnalysis']

# Gemini AI Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-pro")

# Bot details
TOKEN =os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = '@Kkela_bot'

# Feature: Web Search
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not users_collection.find_one({"chat_id": user.id}):
        user_data = {
            "first_name": user.first_name,
            "username": user.username,
            "chat_id": user.id,
        }
        users_collection.insert_one(user_data)
        await update.message.reply_text("Welcome! Your details have been saved.")
    else:
        await update.message.reply_text("Welcome back!")

    await update.message.reply_text("Hello! Thanks for chatting with me. I am a Kela!")

async def request_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact_button = KeyboardButton("Share your phone number", request_contact=True)
    custom_keyboard = [[contact_button]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "Please share your phone number to complete registration:",
        reply_markup=reply_markup,
    )

async def save_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        chat_id = update.message.from_user.id
        users_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"phone_number": phone_number}},
        )
        await update.message.reply_text("Thank you! Your phone number has been saved.")
    else:
        await update.message.reply_text("Please use the contact button to share your phone number.")

# Feature: Gemini AI Chat
async def gemini_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        response = gemini_model.generate_content(user_input)
        bot_response = response.text if response else "Sorry, I couldn't process that."

        chat_history_collection.insert_one({
            "chat_id": update.message.chat_id,
            "user_input": user_input,
            "bot_response": bot_response,
            "timestamp": datetime.datetime.utcnow()
        })

        await update.message.reply_text(bot_response)
    except Exception as e:
        await update.message.reply_text("Error processing your request.")
        print(f"Gemini API Error: {e}")

# Feature: Handle Image/File Analysis
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document or update.message.photo[-1]
    file_id = file.file_id
    file_unique_id = file.file_unique_id
    file_path = await context.bot.get_file(file_id)

    file_metadata = {
        "chat_id": update.message.chat_id,
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "file_path": file_path.file_path,
        "timestamp": datetime.datetime.utcnow()
    }

    try:
        response = gemini_model.generate_content(f"Describe this file: {file_path.file_path}")
        file_metadata["description"] = response.text if response else "No description available."
    except Exception as e:
        file_metadata["description"] = "Error processing file."
        print(f"Gemini File Analysis Error: {e}")

    file_analysis_collection.insert_one(file_metadata)
    await update.message.reply_text(f"File analyzed: {file_metadata['description']}")



async def web_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a search query. Example: /websearch AI trends")
        return

    query = ' '.join(context.args)
    
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_SEARCH_API_KEY}&cx={SEARCH_ENGINE_ID}"

    try:
        response = requests.get(url)
        data = response.json()

        if "items" in data:
            search_results = [
                f"{i+1}. [{item['title']}]({item['link']})\n_{item.get('snippet', 'No description available.')}_"
                for i, item in enumerate(data["items"][:5])
            ]

            # Prepare text for AI summary
            search_text = "\n".join([f"{item['title']}: {item.get('snippet', '')}" for item in data["items"][:5]])

            # Generate summary using Gemini AI
            
            response = gemini_model.generate_content(f"Summarize the following search results:\n{search_text}")
            summary = response.text if response.text else "No summary available."

            # Send the response
            message = f"🔎 **Search Summary:**\n_{summary}_\n\n**Top Search Results for:** `{query}`\n\n" + "\n".join(search_results)
            await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

        else:
            await update.message.reply_text("No results found.")
    
    except Exception as e:
        await update.message.reply_text("⚠️ Error fetching search results.")
        print(f"Web Search Error: {e}")
    
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

if __name__ == '__main__':
    print("Starting bot...")

    app = Application.builder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("get_phone", request_phone_number))
    app.add_handler(CommandHandler("websearch", web_search))
    app.add_handler(MessageHandler(filters.CONTACT, save_phone_number))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gemini_chat))
    app.add_handler(MessageHandler(filters.PHOTO | filters.ATTACHMENT, handle_file))
    app.add_error_handler(error)

    print("Polling...")
    app.run_polling(poll_interval=5,timeout=60)
