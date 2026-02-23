from telegram import Update
from telegram.ext import ContextTypes

import os
import subprocess
from telegram import Update
from telegram.ext import ContextTypes

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for the /start command with the 'Butler' persona.
    """
    welcome_message = (
        "*(Note: I'm currently waiting for a Brave Search key for native search, but I can still fetch any URL you give me).* \n\n"
        "• **System Mastery:** I can run shell commands, manage background processes, and interact with your filesystem directly on the Azure VM.\n"
        "• **Task Management & Memory:** I maintain a long-term memory and daily logs.\n\n"
        "🧩 **Specialized Skills (The 'Butler' Toolkit)**\n"
        "I'm pre-configured for:\n"
        "• **Weather:** For when you're considering touching grass.\n"
        "• **Healthcheck:** To keep this deployment secure and hardened.\n\n"
        "What's the first order of business, Sir? Should we start on an app, or do you have a specific research rabbit hole you'd like me to dive into?"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Advanced handler for JARVIS.
    """
    user_input = update.message.text.lower()
    
    # 1. Cloud Awareness Check
    if "running on cloud" in user_input or "where are you" in user_input:
        response = (
            "Yes, Sir. I am currently running on your **Azure Ubuntu VM (Standard B2ats v2)** in Central India.\n"
            "Public IP: `74.225.248.54`\n"
            "Persistence is managed by **PM2**. I am ready for 24/7 duty."
        )
    
    # 2. Healthcheck Skill
    elif "healthcheck" in user_input or "status" in user_input:
        try:
            # Simple check of memory availability on the VM
            mem_info = subprocess.check_output(['free', '-m']).decode('utf-8')
            response = f"Systems are nominal, Sir.\n\n**Memory Status:**\n`{mem_info}`"
        except Exception as e:
            response = f"I encountered an issue checking system health: {str(e)}"

    # 3. Default Persona Response
    else:
        response = (
            f"I've noted your message: *\"{update.message.text}\"*.\n\n"
            "I'm currently in 'Observer Mode' while we finalize the OpenClaw bridge integration. "
            "Would you like me to perform a **Healthcheck** or check the **Weather**?"
        )
    
    await update.message.reply_text(response, parse_mode='Markdown')

