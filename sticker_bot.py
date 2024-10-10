import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Fetch the API token from the environment variable
API_TOKEN = os.getenv('API_TOKEN')  # This will fetch the API token from the environment variable

if API_TOKEN is None:
    raise ValueError("API_TOKEN environment variable not set. Please set it in the Koyeb environment.")

# Now you can use the API_TOKEN in your script as needed
print("Using API Token:", API_TOKEN)  # For debugging purposes (remove or comment out in production)

# API_TOKEN = ''   Replace with your bot token

def start(update: Update, context: CallbackContext) -> None:
    """Send a greeting message and prompt user to choose an option."""
    user_first_name = update.message.from_user.first_name  # Get the user's first name
    user_id = update.message.from_user.id  # Get the user's ID

    # Send a greeting message with HTML formatting
    welcome_message = (
        "<b>Welcome to the Sticker Bot!</b> 🎉\n\n"
        f"Hello there, <a href='tg://user?id={user_id}'>{user_first_name}</a>! I'm here to help you with all your sticker needs on Telegram. "
        "Whether you're a sticker enthusiast or just looking to have some fun, you've come to the right place!\n\n"
        "<b>Here’s what I can do for you:</b>\n"
        "<b>- View Stickers:</b> <i>Send me a sticker ID, and I’ll show you the sticker right away!\n</i>"
        "<b>- Get Sticker ID:</b> <i>Just send me any sticker, and I’ll tell you its unique ID.\n</i>"
        "<b>- Sticker Details:</b> <i>Send me a sticker, and I’ll provide you with detailed information about it, "
        "including its ID, associated emoji, and a link to its sticker pack.</i>"
    )

    update.message.reply_text(welcome_message, parse_mode='HTML')

    # Create inline keyboard
    keyboard = [
        [InlineKeyboardButton("View Sticker", callback_data='view_sticker'),
         InlineKeyboardButton("Get Sticker ID", callback_data='get_sticker_id')],
        [InlineKeyboardButton("Sticker Details", callback_data='sticker_details')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the options
    update.message.reply_text('Choose an option:', reply_markup=reply_markup)


def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle button clicks."""
    query = update.callback_query
    query.answer()

    if query.data == 'view_sticker':
        query.edit_message_text(text="Please send me the sticker ID to view the sticker.")
        context.user_data['action'] = 'view_sticker'
    elif query.data == 'get_sticker_id':
        query.edit_message_text(text="Please send me the sticker.")
        context.user_data['action'] = 'get_sticker_id'
    elif query.data == 'sticker_details':
        query.edit_message_text(text="Please send me the sticker.")
        context.user_data['action'] = 'sticker_details'


def handle_sticker(update: Update, context: CallbackContext) -> None:
    """Handle the sticker sent by the user."""
    if 'action' not in context.user_data:
        update.message.reply_text("Please choose an option first using /start.")
        return

    action = context.user_data['action']

    if action == 'view_sticker':
        sticker_id = update.message.text.strip()  # Get the sticker ID from the message text
        update.message.reply_sticker(sticker_id)  # Reply with the sticker ID
        context.user_data.pop('action')  # Clear action after handling

    elif action == 'get_sticker_id':
        sticker_id = update.message.sticker.file_id
        update.message.reply_text(f'Sticker ID: `{sticker_id}`', parse_mode='Markdown')
        context.user_data.pop('action')  # Clear action after handling

    elif action == 'sticker_details':
        sticker_id = update.message.sticker.file_id
        emoji = update.message.sticker.emoji or "No emoji"

        # Assuming the sticker is part of a sticker pack, we get the set name if available.
        sticker_set_name = update.message.sticker.set_name if update.message.sticker.set_name else "No sticker pack"

        # Create the sticker pack link if applicable
        sticker_pack_link = f"https://t.me/addstickers/{sticker_set_name}" if sticker_set_name != "No sticker pack" else "N/A"

        # Send sticker details
        details_message = (
            f"**Sticker ID:** `{sticker_id}`\n"
            f"**Emoji:** {emoji}\n"
            f"**Sticker Pack:** {sticker_set_name}\n"
            f"**Pack Link:** [Link]({sticker_pack_link})" if sticker_pack_link != "N/A" else "No pack link available."
        )
        update.message.reply_text(details_message, parse_mode='Markdown')
        context.user_data.pop('action')  # Clear action after handling


def main() -> None:
    """Start the bot."""
    updater = Updater(API_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.sticker, handle_sticker))
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, handle_sticker))  # Handle text input for sticker IDs

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal (Ctrl+C)
    updater.idle()


if __name__ == '__main__':
    main()
