from typing import Final
from telegram import Update
from telegram.ext import Application,ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN='7674929245:AAHutXT-YM8M-CbR0oD7BSbXtUkXXsnIroo'
BOT_USERNAME: Final='@Kkela_bot'
# Commands
async def start_command(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello Thanks for chatting with me! I am a Kela!')
async def help_command(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('I am a Banana ')
async def custom_command(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is a custom command')


# Response 
def handle_response(text:str)->str:
    processed:str=text.lower()
    if 'hello' in processed :
        return 'Hello!'
    
    if 'How are you ' in processed:
        return 'I am good '
    else:
        return 'I am a Kela!'
async def handle_message(update:Update,context:ContextTypes.DEFAULT_TYPE):
    message_type: str=update.message.chat.type
    text:str=update.message.text
    print(f'({update.message.chat.id}) in {message_type}:"{text}"')
    if message_type=='group':
        if BOT_USERNAME in text:
            new_text=text.replace(BOT_USERNAME,'').strip()
            response:str=handle_response(new_text)
        else:
            return 
    else:
        response:str=handle_response(text)
    print('Bot',response)
    await update.message.reply_text(response)

async def error(update:Update,context:ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused erroe {context.error}')

if __name__=='__main__':
    print('Strating bot.....')

    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start',start_command))
    app.add_handler(CommandHandler('help',help_command))
    app.add_handler(CommandHandler('custom',custom_command))
    # Messsages
    app.add_handler(MessageHandler(filters.TEXT,handle_message))
    # Errors
    app.add_error_handler(error)
    # Polls the bot   
    print('Polling')
    app.run_polling(poll_interval=3)