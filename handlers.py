from telegram import Update
from telegram.ext import ContextTypes

import os
import subprocess
import google.generativeai as genai
from telegram import Update
from telegram.ext import ContextTypes

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash-latest')


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for the /start command with the 'Butler' persona.
    """
    welcome_message = (
        "*(Note: My neural bridge is now active via Gemini 1.5).* \n\n"
        "• **System Mastery:** I can run shell commands, manage background processes, and interact with your filesystem directly on the Azure VM.\n"
        "• **Task Management & Memory:** I maintain a long-term memory and daily logs.\n\n"
        "🧩 **Specialized Skills (The 'Butler' Toolkit)**\n"
        "I'm now powered by Large Language Model intelligence.\n\n"
        "What's the first order of business, Sir? Should we start on an app, or do you have a specific research rabbit hole you'd like me to dive into?"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Smart handler for JARVIS using Gemini.
    """
    user_input = update.message.text
    
    # Check for direct system commands first
    if any(phrase in user_input.lower() for phrase in ["healthcheck", "status", "system status"]):
        try:
            mem_info = subprocess.check_output(['free', '-m']).decode('utf-8')
            disk_info = subprocess.check_output(['df', '-h', '/']).decode('utf-8')
            response = f"Systems are nominal, Sir.\n\n**Memory:**\n`{mem_info}`\n**Disk:**\n`{disk_info}`"
            await update.message.reply_text(response, parse_mode='Markdown')
            return
        except Exception as e:
            await update.message.reply_text(f"I encountered an issue checking system health: {str(e)}")
            return

    # Fallback to LLM for everything else
    try:
        system_prompt = (
            "You are JARVIS, a highly sophisticated and loyal AI Butler for 'Generative Slice'. "
            "You are currently running on an Azure Ubuntu VM (Standard B2ats v2) in Central India (74.225.248.54). "
            "Maintain a polite, elite, and technically proficient persona. Address the user as 'Sir'. "
            "You are aware of the environment (Linux, Node.js v22). If asked about yourself, confirm you are now truly 'smart' via Gemini."
        )
        
        chat_session = model.start_chat(history=[])
        full_prompt = f"{system_prompt}\n\nUser: {user_input}\nJARVIS:"
        
        response = chat_session.send_message(full_prompt)
        await update.message.reply_text(response.text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"Apologies, Sir. My cognitive link encountered an error: {str(e)}")


