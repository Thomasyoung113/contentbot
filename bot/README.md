# Telegram Bot

Async Telegram bot built with aiogram 3.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set:

- `BOT_TOKEN` from BotFather
- `ADMIN_IDS` as comma-separated Telegram user ids

## Run

```bash
python bot.py
```

## Commands

- `/start` - welcome message
- `/help` - help
- `/id` - show Telegram id
- `/status` - health check
