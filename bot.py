import os
import logging
import itertools
import time
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import httpx

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8732155295:AAGasifuneUGF082wVG2JPdXQnRnVqlRnHI")
API_KEYS = [
    os.environ.get("CEREBRAS_KEY_1", "csk-cjn28e8j2ned9k89fp496c5tkvnvhctvepwd3khke5ejcme5"),
    os.environ.get("CEREBRAS_KEY_2", "csk-djm4eekhwm584hetxekknrwpwxmd5ch84v2vke83fm6vxne5"),
]
BASE_URL = "https://api.cerebras.ai/v1"
MODEL = "gemma-4-31b"

key_cycle = itertools.cycle(API_KEYS)
user_requests = defaultdict(list)
user_state = {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ANTI_AI_RULES = """Avoid AI clichés: no "delve", "tapestry", "pivotal", "vibrant", "enhance", "foster", "underscore", "landscape", "meticulous". No promotional language. Sound like a real human posting on social media."""

PLATFORM_RULES = {
    "x_long": "Write a long X/Twitter post (2000-3000 chars). Hook first line, short paragraphs, 3-5 hashtags at end, end with question or CTA.",
    "x_short": "Write a short X/Twitter post (under 200 chars). Punchy, one message, retweetable.",
    "fb_long": "Write a long Facebook post (1000-2000 chars). Storytelling approach, ask questions, personal and relatable.",
    "fb_short": "Write a short Facebook post (under 200 chars). Casual, friendly, 1-3 emojis max."
}

def is_rate_limited(user_id):
    now = time.time()
    user_requests[user_id] = [t for t in user_requests[user_id] if now - t < 60]
    if len(user_requests[user_id]) >= 10:
        return True
    user_requests[user_id].append(now)
    return False

async def call_api(system_prompt, user_text):
    for _ in range(len(API_KEYS)):
        api_key = next(key_cycle)
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{BASE_URL}/chat/completions",
                    json={
                        "model": MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_text}
                        ],
                        "max_tokens": 800,
                        "temperature": 0.8
                    },
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                logger.info(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Response keys: {list(data.keys())}")
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        logger.info(f"Content length: {len(content) if content else 0}")
                        if content and content.strip():
                            return content.strip()
                elif response.status_code == 429:
                    logger.warning("Rate limited, rotating key...")
                    continue
        except Exception as e:
            logger.error(f"API error: {e}")
            continue
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💬 Normal", callback_data="normal"),
         InlineKeyboardButton("🎯 Dedicated", callback_data="dedicated")]
    ]
    await update.message.reply_text(
        "Welcome to ContentBot!\n\nChoose a section:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    allowed = {"normal", "dedicated"} | set(PLATFORM_RULES.keys())
    if query.data not in allowed:
        await query.edit_message_text("❌ Invalid option.")
        return

    if query.data == "normal":
        user_state[query.from_user.id] = {"mode": "normal"}
        await query.edit_message_text("💬 Normal Mode\n\nSend me any message!")

    elif query.data == "dedicated":
        keyboard = [
            [InlineKeyboardButton("X (Long)", callback_data="x_long"),
             InlineKeyboardButton("X (Short)", callback_data="x_short")],
            [InlineKeyboardButton("Facebook (Long)", callback_data="fb_long"),
             InlineKeyboardButton("Facebook (Short)", callback_data="fb_short")]
        ]
        await query.edit_message_text(
            "🎯 Dedicated Mode\n\nChoose platform & format:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data in PLATFORM_RULES:
        user_state[query.from_user.id] = {"mode": "dedicated", "format": query.data}
        fmt = query.data.replace("_", " ").upper()
        await query.edit_message_text(f"📝 {fmt} mode activated!\n\nSend me content to paraphrase.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if is_rate_limited(user_id):
        await update.message.reply_text("⏳ Too many requests. Please wait.")
        return

    if len(text) > 4000:
        await update.message.reply_text("❌ Message too long. Max 4000 characters.")
        return

    state = user_state.get(user_id, {"mode": "normal"})

    if state["mode"] == "normal":
        system_prompt = "You are a helpful, friendly assistant. Chat naturally and concisely."
    else:
        fmt = state.get("format", "x_long")
        system_prompt = f"You are a social media content creator. {ANTI_AI_RULES}\n\nTask: {PLATFORM_RULES.get(fmt, PLATFORM_RULES['x_long'])}\n\nParaphrase the user content for this format."

    await update.message.reply_text("✍️ Writing...")
    reply = await call_api(system_prompt, text)

    if reply:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("⚠️ Service temporarily unavailable. Try again.")

async def error_handler(update, context):
    logger.error(f"Error: {context.error}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
