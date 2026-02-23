from telegram import Update
from telegram.ext import ContextTypes

import os
import subprocess
import asyncio
from google import genai
from telegram import Update
from telegram.ext import ContextTypes

# playwright will be used for screenshots
from playwright.async_api import async_playwright

# Configure Gemini Client
client = genai.Client()

async def take_screenshot(url: str, output_path: str):
    """
    Captures a screenshot of a given URL.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        # Wait for potential animations or load
        await asyncio.sleep(2)
        await page.screenshot(path=output_path)
        await browser.close()

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for the /start command with the 'Butler' persona.
    """
    welcome_message = (
        "*(Note: My neural bridge is now fully equipped for visual and terminal tasks).* \n\n"
        "• **System Mastery:** I can run shell commands, manage background processes, and interact with your filesystem directly on the Azure VM.\n"
        "• **Visual Feedback:** I can capture screenshots of your local apps or external sites and send them directly to this chat.\n\n"
        "Sir, should we begin with a technical demonstration (cloning a project or running a test), or do you have a specific target in mind?"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Advanced handler for JARVIS that supports integrated task execution.
    """
    user_input = update.message.text
    
    # Check for direct system status commands
    if any(phrase in user_input.lower() for phrase in ["healthcheck", "status", "system status"]):
        try:
            mem_info = subprocess.check_output(['free', '-h']).decode('utf-8')
            disk_info = subprocess.check_output(['df', '-h', '/']).decode('utf-8')
            response = f"Systems are nominal, Sir.\n\n**Memory:**\n`{mem_info}`\n**Disk:**\n`{disk_info}`"
            await update.message.reply_text(response, parse_mode='Markdown')
            return
        except Exception as e:
            await update.message.reply_text(f"I encountered an issue checking system health: {str(e)}")
            return

    # LLM Interaction
    try:
        system_prompt = (
            "You are JARVIS, the loyal AI Butler for 'Generative Slice'. "
            "You run on an Azure Ubuntu VM (74.225.248.54). "
            "Maintain an elite, technisch competent, and polite persona. Address the user as 'Sir'. "
            "You have the capability to execute shell commands and take screenshots. "
            "If the user wants you to do a task like cloning a repo, running a project, or taking a screenshot, "
            "provide your response, and then on a NEW LINE, use one of these tags if needed:\n"
            "RUN_CMD: <command>\n"
            "SCREENSHOT: <url>\n\n"
            "Example: 'Certainly, Sir. I am cloning the repository now.\nRUN_CMD: git clone ...'"
        )
        
        full_prompt = f"{system_prompt}\n\nUser: {user_input}\nJARVIS:"
        
        # We'll use the prompt directly for now
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=full_prompt
        )
        jarvis_reply = response.text
        
        # Let the user know JARVIS is thinking/acting
        await update.message.reply_text(jarvis_reply, parse_mode='Markdown')

        # Simple parser for the model's 'actions'
        for line in jarvis_reply.split('\n'):
            if line.startswith("RUN_CMD:"):
                cmd = line.replace("RUN_CMD:", "").strip()
                try:
                    process_output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
                    await update.message.reply_text(f"**Execution Output, Sir:**\n`{process_output[:1000]}`", parse_mode='Markdown')
                except subprocess.CalledProcessError as e:
                    await update.message.reply_text(f"Sir, the command failed with error:\n`{e.output.decode('utf-8')[:1000]}`", parse_mode='Markdown')
            
            elif line.startswith("SCREENSHOT:"):
                url = line.replace("SCREENSHOT:", "").strip()
                temp_img = "screenshot.png"
                await update.message.reply_text(f"Capturing visual data from {url}, please hold, Sir...")
                try:
                    await take_screenshot(url, temp_img)
                    with open(temp_img, "rb") as photo:
                        await update.message.reply_photo(photo=photo, caption=f"Visual data from {url}, Sir.")
                    os.remove(temp_img)
                except Exception as e:
                    await update.message.reply_text(f"I apologize, Sir. My visual sensors failed: {str(e)}")
        
    except Exception as e:
        await update.message.reply_text(f"Apologies, Sir. My cognitive link encountered an error: {str(e)}")



