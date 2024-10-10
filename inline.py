from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
import logging
import re
import random
import threading
import time
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


# Define states
CHANNEL, POST, BUTTON_COUNT, ROWS_SETUP, BUTTON_LABEL, BUTTON_URL = range(6)

# Global variables to store user input and message IDs
user_data = {}
greeting_message_id = None


BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Bot token is not set")


def start(update: Update, context: CallbackContext) -> int:
    global greeting_message_id

    # Create inline buttons
    keyboard = [
        [InlineKeyboardButton("Channel", callback_data='channel'), InlineKeyboardButton("Update", callback_data='update')],
        [InlineKeyboardButton("Reaction", callback_data='reaction')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the initial greeting message with inline buttons
    greeting_message = update.message.reply_text(
        "Hello! I'm alive🌟 And ready to assist you with enhancing your channel post with inline buttons.",
        reply_markup=reply_markup
    )

    # Store the message ID for later deletion
    greeting_message_id = greeting_message.message_id

    return CHANNEL



def send_instruction(update: Update, context: CallbackContext) -> None:
    # Delete the greeting message if it exists
    if greeting_message_id:
        try:
            context.bot.delete_message(chat_id=update.message.chat_id, message_id=greeting_message_id)
        except Exception as e:
            logger.error(f"Failed to delete greeting message: {e}")

    # Send the instruction message
    update.message.reply_text(
        "Welcome! To enhance a channel post with inline buttons, please follow the prompts.\n"
        "First, send me the channel username (e.g., @yourchannel) or the channel link (e.g., https://t.me/yourchannel).\n"
        "For private channels, send the full post link (e.g., https://t.me/c/2241403405/51)."
    )


def get_channel(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    public_channel_pattern = re.compile(r"https://t\.me/(\S+)")
    private_channel_pattern = re.compile(r"https://t\.me/c/(\d+)/(\d+)")  # Private channel pattern

    # Check if the input is a private channel post link
    if private_channel_pattern.match(user_input):
        match = private_channel_pattern.match(user_input)
        user_data['channel'] = '-100' + match.group(1)  # For private channels, prefix the channel ID with -100
        user_data['post_id'] = match.group(2)
        update.message.reply_text("Great! You have provided a private channel post link. \nNow how many inline buttons would you like to add? Please send a number (maximum 100)")
        return BUTTON_COUNT  # Skip post input since it's already in the private link

    # Check for public channel username or link
    elif public_channel_pattern.match(user_input):
        match = public_channel_pattern.match(user_input)
        user_data['channel'] = '@' + match.group(1)
    elif user_input.startswith('@'):
        user_data['channel'] = user_input
    else:
        update.message.reply_text(
            "Invalid input. Please send a valid channel username (e.g., @yourchannel) or channel link."
        )
        return CHANNEL

    update.message.reply_text(
        "Great! Now send me the post ID of the message you want to enhance, or the post link (e.g., https://t.me/yourchannel/123)."
    )
    return POST


def get_post(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    post_pattern = re.compile(r"https://t\.me/(\S+)/(\d+)")

    if post_pattern.match(user_input):
        match = post_pattern.match(user_input)
        user_data['channel'] = '@' + match.group(1)
        user_data['post_id'] = match.group(2)
    else:
        try:
            user_data['post_id'] = int(user_input)
        except ValueError:
            update.message.reply_text(
                "Invalid input. Please send a valid post ID or post link."
            )
            return POST

    update.message.reply_text(
        "How many inline buttons would you like to add? Please send a number (maximum 100)."
    )
    return BUTTON_COUNT


def get_button_count(update: Update, context: CallbackContext) -> int:
    try:
        button_count = int(update.message.text)
        if button_count > 100:
            update.message.reply_text(
                "You can add up to 100 buttons only. Please send a valid number."
            )
            return BUTTON_COUNT
        user_data['button_count'] = button_count
        user_data['buttons'] = []
        user_data['current_button'] = 0

        if button_count == 1:
            update.message.reply_text(
                "You have selected 1 button. Now, send me the label for the button."
            )
            return BUTTON_LABEL
        else:
            user_data['button_rows'] = []
            update.message.reply_text(
                "Specify the number of buttons for each row. Start by sending the number of buttons for the first row."
            )
            return ROWS_SETUP
    except ValueError:
        update.message.reply_text(
            "Invalid input. Please send a valid number."
        )
        return BUTTON_COUNT


def setup_rows(update: Update, context: CallbackContext) -> int:
    try:
        row_count = int(update.message.text)
        if row_count <= 0:
            update.message.reply_text(
                "The number of buttons per row must be positive. Please send a valid number."
            )
            return ROWS_SETUP

        total_buttons = sum(user_data['button_rows'])
        if total_buttons + row_count > user_data['button_count']:
            update.message.reply_text(
                f"The total number of buttons cannot exceed {user_data['button_count']}. Please adjust the number."
            )
            return ROWS_SETUP

        user_data['button_rows'].append(row_count)

        if sum(user_data['button_rows']) < user_data['button_count']:
            update.message.reply_text(
                "How many buttons would you like in the next row? Please send a number."
            )
            return ROWS_SETUP
        else:
            update.message.reply_text(
                "Row setup complete. Now, send me the label for button 1."
            )
            return BUTTON_LABEL
    except ValueError:
        update.message.reply_text(
            "Invalid input. Please send a valid number."
        )
        return ROWS_SETUP


def get_button_label(update: Update, context: CallbackContext) -> int:
    user_data['current_label'] = update.message.text
    update.message.reply_text(
        f"Got it! Now send me the URL for button {user_data['current_button'] + 1}."
    )
    return BUTTON_URL


def is_valid_url(url):
    regex = re.compile(
        r'^(?:(?:http|ftp)s?://'  # Optional http:// or https://
        r'|(?:www\.)?'  # Optional www.
        r'|)'  # Allow empty to capture plain domains
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # Domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # Optional port
        r'(?:/?|[/?]\S+)?$'  # Optional path/query
    , re.IGNORECASE)  # Case insensitive matching
    return re.match(regex, url) is not None


def get_button_url(update: Update, context: CallbackContext) -> int:
    url = update.message.text
    if not is_valid_url(url):
        update.message.reply_text("Invalid URL. Please provide a valid URL for the button.")
        return BUTTON_URL

    label = user_data['current_label']
    user_data['buttons'].append((label, url))
    user_data['current_button'] += 1

    if user_data['current_button'] < user_data['button_count']:
        update.message.reply_text(
            f"Send me the label for button {user_data['current_button'] + 1}."
        )
        return BUTTON_LABEL
    else:
        update.message.reply_text(
            "All buttons received! Adding them to the post..."
        )
        add_inline_buttons(update, context)
        return ConversationHandler.END



def add_inline_buttons(update: Update, context: CallbackContext) -> None:
    channel = user_data['channel']
    post_id = int(user_data['post_id'])
    button_rows = user_data.get('button_rows', [1])
    buttons = user_data['buttons']

    inline_keyboard = []
    index = 0
    for row_count in button_rows:
        row = []
        for _ in range(row_count):
            if index < len(buttons):
                label, url = buttons[index]
                row.append(InlineKeyboardButton(label, url=url))
                index += 1
        inline_keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(inline_keyboard)

    context.bot.edit_message_reply_markup(
        chat_id=channel, message_id=post_id, reply_markup=reply_markup
    )
    update.message.reply_text("Inline buttons added successfully!")


def check_alive(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("I'm alive and running! 🌟")


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Process cancelled.")
    return ConversationHandler.END


def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    logger.info(f"Button pressed: {query.data}")  # Log button press

    if query.data == 'channel':
        query.edit_message_text(text="Please send me the channel username (e.g., @yourchannel) or the channel link (e.g., https://t.me/yourchannel).\n For Private Channel Just send me the post link")
        return CHANNEL
    elif query.data == 'update':
        # This will show a pop-up alert message
        query.answer(text="🔔 New Update Comming Soon!", show_alert=True)
    elif query.data == 'reaction':
        # This will show a pop-up alert message
        query.answer(text="🔔 Comming Soon!", show_alert=True)

def main() -> None:
    # Initialize the Updater and Dispatcher using the token from config.py
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Register the button handler
    dispatcher.add_handler(CallbackQueryHandler(button_handler))

    # Define conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHANNEL: [MessageHandler(Filters.text & ~Filters.command, get_channel)],
            POST: [MessageHandler(Filters.text & ~Filters.command, get_post)],
            BUTTON_COUNT: [MessageHandler(Filters.text & ~Filters.command, get_button_count)],
            ROWS_SETUP: [MessageHandler(Filters.text & ~Filters.command, setup_rows)],
            BUTTON_LABEL: [MessageHandler(Filters.text & ~Filters.command, get_button_label)],
            BUTTON_URL: [MessageHandler(Filters.text & ~Filters.command, get_button_url)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('alive', check_alive))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
