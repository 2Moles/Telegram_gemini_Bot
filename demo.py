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

# MongoDB setup
client = MongoClient(
"mongodb+srv://mybtp:mybtp@node-api.cqbp1.mongodb.net/?retryWrites=true&w=majority&appName=Node-API"
)
db = client['Telegram']
users_collection = db['Task']

# Bot details
TOKEN = '7674929245:AAHutXT-YM8M-CbR0oD7BSbXtUkXXsnIroo'
BOT_USERNAME: Final = '@Kkela_bot'


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    # Check if the user is already in the database
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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I am a Banana! Here to assist you!")


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("This is a custom command.")


# Feature 2: Request and Save Phone Number
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
        # Update user data in MongoDB
        users_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"phone_number": phone_number}},
        )
        await update.message.reply_text("Thank you! Your phone number has been saved.")
    else:
        await update.message.reply_text("Please use the contact button to share your phone number.")


# Message Responses
def handle_response(text: str) -> str:
    processed: str = text.lower()
    if 'hello' in processed:
        return 'Hello!'
    if 'how are you' in processed:
        return 'I am good!'
    else:
        return 'I am a Kela!'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    print(f'({update.message.chat.id}) in {message_type}:"{text}"')

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)

    print('Bot:', response)
    await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")


if __name__ == '__main__':
    print("Starting bot...")

    app = Application.builder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("custom", custom_command))
    app.add_handler(CommandHandler("get_phone", request_phone_number))
    app.add_handler(MessageHandler(filters.CONTACT, save_phone_number))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_error_handler(error)

    # Polling
    print("Polling...")
    app.run_polling(poll_interval=3)
