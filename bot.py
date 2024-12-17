import os
import requests
import logging
from flask import Flask, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('URL')

# Validate environment variables
if not API_KEY:
    raise ValueError("API_KEY is not set. Check your environment variables.")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL is not set. Check your environment variables.")

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

# Telegram API call function
def bot(method, data=None):
    url = f"https://api.telegram.org/bot{API_KEY}/{method}"
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Telegram API: {e}")
        return None

# Function to handle /start command
def handle_start_command(chat_id):
    message = "*🇺🇸 Hi there.* \nAdd me as an admin to your channel, and I'll automatically approve all user join requests."
    bot('sendMessage', {
        'chat_id': chat_id,
        'parse_mode': 'markdown',
        'text': message
    })

# Function to handle join requests
def approve_join_request(join_request):
    chat_id = join_request['chat']['id']
    user_id = join_request['from']['id']
    first_name = join_request['from']['first_name']
    chat_title = join_request['chat']['title']

    # Approve the join request
    approve_response = bot("approveChatJoinRequest", {
        "chat_id": chat_id,
        "user_id": user_id
    })

    if approve_response and approve_response.get('ok'):
        message = f"👋 Hello <b>{first_name}</b>,\nYour request to join channel <b>{chat_title}</b> has been approved! 🎉"
        reply_markup = {
            "inline_keyboard": [
                [{"text": "Visit Our Channel", "url": "https://t.me/anuj_bots"}]
            ]
        }
        bot('sendMessage', {
            'chat_id': user_id,
            'parse_mode': 'html',
            'text': message,
            'reply_markup': reply_markup
        })
    else:
        logger.error(f"Failed to approve join request for user {user_id} in chat {chat_id}.")

# Main function to process updates
def process_update(update):
    try:
        message = update.get('message')
        chat_join_request = update.get('chat_join_request')

        if message:
            chat_id = message['chat']['id']
            text = message.get('text', '')

            if text == "/start":
                handle_start_command(chat_id)

        if chat_join_request:
            approve_join_request(chat_join_request)

    except KeyError as e:
        logger.error(f"Missing expected field in update: {e}")

# Webhook endpoint
@app.route(f"/webhook/{API_KEY}", methods=["POST"])
def webhook():
    try:
        update = request.get_json()  # Parse the incoming webhook payload
        process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
    return "OK", 200

# Set webhook (one-time setup)
def set_webhook():
    webhook_url = f"{WEBHOOK_URL}/webhook/{API_KEY}"
    response = bot("setWebhook", {"url": webhook_url})
    if response and response.get("ok"):
        logger.info("Webhook set successfully!")
    else:
        logger.error(f"Failed to set webhook: {response}")

if __name__ == "__main__":
    # Uncomment the line below to set the webhook during deployment
    # unset_webhook()
    set_webhook()

    # Start Flask server
    app.run(host="0.0.0.0", port=5000)
