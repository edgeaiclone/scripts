from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext

# Replace with your bot's API token
API_TOKEN = 'YOUR_API_TOKEN'

# Function to handle incoming messages
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id  # Get the user_id of the sender
    username = update.message.from_user.username  # Get the username of the sender
    print(f"User ID: {user_id}, Username: {username}")  # Print to console
    update.message.reply_text(f"Hello {username}, your user ID is {user_id}.")

# Set up the Updater and Dispatcher
def main() -> None:
    # Initialize the Updater with your bot's token
    updater = Updater(API_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register a command handler for the /start command
    dispatcher.add_handler(CommandHandler("start", start))

    # Register a message handler that triggers on any message
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    # Start polling for updates from Telegram
    updater.start_polling()

    # Run the bot until the user presses Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
