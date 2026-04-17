# Jarvis 🤖

A Telegram-based AI butler bot powered by Google Gemini. Jarvis responds to natural-language prompts, executes shell commands on your server, and captures screenshots — all via Telegram chat.

---

## Features

* 💬 **Conversational AI** — Powered by Gemini; responds to any free-text message.
* 🖥️ **Shell Command Execution** — Runs server-side commands and returns output directly in chat.
* 📸 **Screenshot Capture** — Takes screenshots of local or external URLs via Playwright.
* ❤️ **System Health Check** — Reports memory and disk usage on demand.
* 🔒 **Markdown-safe replies** — Automatically falls back to plain text if formatting fails.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **Telegram** | `python-telegram-bot >= 20.0` |
| **AI Model** | Google Gemini (`google-genai`) |
| **Screenshots** | Playwright (Chromium) |
| **Config** | `python-dotenv` |

---

## Prerequisites

* Python 3.10 or higher
* A Telegram bot token (from [@BotFather](https://t.me/BotFather))
* A [Google Gemini API key](https://aistudio.google.com/app/apikey)
* Linux environment recommended (uses `free` and `df` system commands)

---

## Installation

```bash
# 1. Clone the repository
git clone [https://github.com/smdhussain06/Jarvis.git](https://github.com/smdhussain06/Jarvis.git)
cd Jarvis

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browser binaries
python -m playwright install chromium

# On Linux, if you get missing-dependency errors:
python -m playwright install-deps chromium
