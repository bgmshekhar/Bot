from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os
import requests
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the bot application
application = Application.builder().token(TOKEN).build()

# Command to start the bot
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(GoogleTranslator(source='auto', target='en').translate("Hello! I'm your AI-backed Telegram bot for Victory Express."))

# Command to display help message
async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text("This is the help message.")

# Function to clean and format the bullet points
def clean_bullet_points(bullet_points):
    cleaned_points = []
    for point in bullet_points:
        point = point.strip()
        if point and not point.startswith("*") and not point.startswith("**"):
            cleaned_points.append(f"• {point}")
    return cleaned_points

# Function to translate text
def translate_text(text, target_language):
    translator = GoogleTranslator(source='auto', target=target_language)
    return translator.translate(text)

# Function to get translation
def get_translation(text):
    translations = {
        "Hello! I'm your AI-backed Telegram bot for Victory Express.": "नमस्ते! मैं आपका विक्ट्री एक्सप्रेस के लिए एआई-संचालित टेलीग्राम बॉट हूँ।",
        "Use /start to get started and /help for commands.": "/start का उपयोग करके शुरू करें और कमांड के लिए /help।",
        "Please specify the subject and chapter. Example: \n`/search Subject: Biology | Chapter: Cell Biology`": "कृपया विषय और अध्याय निर्दिष्ट करें। उदाहरण: \n`/search विषय: जीव विज्ञान | अध्याय: कोशिका जीव विज्ञान`",
    }
    return translations.get(text, text)

# Function to handle the search query and generate AI-backed bullet points
async def search(update: Update, context: CallbackContext):
    query = ' '.join(context.args)

    if not query:
        await update.message.reply_text(get_translation("Please specify the subject and chapter. Example: \n`/search Subject: Biology | Chapter: Cell Biology`"), parse_mode="Markdown")
        return

    try:
        # Translate the user's query
        translated_query = translate_text(query, "en")

        # Correct Google Gemini API URL
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "contents": [{"parts": [{"text": f"Summarize the topic in 50 bullet points: {translated_query}"}]}]
        }

        # Make the API request
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        # Parse the response from Gemini API
        response_json = response.json()
        bullet_points = response_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").split("\n")

        # Clean the bullet points
        cleaned_points = clean_bullet_points(bullet_points)

        # Translate the bot's response
        translated_response = "\n".join([translate_text(point, "hi") for point in cleaned_points])

        # If the message is too long, break it into chunks
        message_chunks = []
        chunk_size = 4096  # Telegram's message size limit
        while translated_response:
            chunk = translated_response[:chunk_size]
            message_chunks.append(chunk)
            translated_response = translated_response[chunk_size:]

        # Send the chunks as multiple messages
        for chunk in message_chunks:
            await update.message.reply_text(chunk)

    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Error: {e}")
    except KeyError:
        await update.message.reply_text("An error occurred while processing the Gemini API response.")

# Add handlers to the application
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("search", search))  # Adding /search command handler

# Run the bot
if __name__ == "__main__":
    application.run_polling()