# University Meetup Bot

Telegram bot for university students to create profiles and meet each other.

## Setup

### 1. Clone and install
```bash
git clone https://github.com/hader239/uni_meet_bot.git
cd uni_meet_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Add bot token
Create a `.env` file:
```
TELEGRAM_BOT_TOKEN=<ask me for the token>
```

### 3. Run
```bash
python bot.py
```

## Commands
- `/start` - Open the main menu
- `/help` - Show help info
