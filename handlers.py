import os
import subprocess
import asyncio
from google import genai
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

# playwright will be used for screenshots
from playwright.async_api import async_playwright

# Configure Gemini Client
client = genai.Client()

async def safe_reply(update: Update, text: str, parse_mode: str = 'Markdown'):
    """
    Attempts to send a reply with Markdown, falling back to plain text if parsing fails.
    """
    try:
        await update.message.reply_text(text, parse_mode=parse_mode)
    except BadRequest:
        # Fallback to plain text if Markdown is broken
        await update.message.reply_text(text, parse_mode=None)

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
    await safe_reply(update, welcome_message)

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
            await safe_reply(update, response)
            return
        except Exception as e:
            await update.message.reply_text(f"I encountered an issue checking system health: {str(e)}")
            return

    # LLM Interaction
    try:
        # We'll use chat_data to store the current working directory for this session
        if 'cwd' not in context.chat_data:
            context.chat_data['cwd'] = os.path.expanduser("~/cloudJarvis")

        system_prompt = (
            "You are JARVIS, the loyal AI Butler for 'Generative Slice'. "
            "You run on an Azure Ubuntu VM (74.225.248.54). "
            "Maintain an elite, technisch competent, and polite persona. Address the user as 'Sir'. "
            "You have the capability to execute shell commands and take screenshots.\n\n"
            "CURRENT WORKING DIRECTORY: " + context.chat_data['cwd'] + "\n\n"
            "IMPORTANT RULES:\n"
            "1. If you need to run multiple dependent commands (e.g., clone and then install), use a SINGLE RUN_CMD block and chain them with &&.\n"
            "2. If you need to change directory permanently for future commands, include 'cd <dir>' in your command AND mention it in text.\n"
            "3. For screenshots of local webapps, ensure the server is running and use 'localhost:<port>'.\n"
            "4. Use exactly these tags at the end of your response:\n"
            "RUN_CMD: <command>\n"
            "SCREENSHOT: <url>\n\n"
            "Example:\n"
            "'Certainly, Sir. I will clone the repository and install dependencies.\n"
            "RUN_CMD: git clone https://github.com/example/repo LiteLabs && cd LiteLabs && npm install'"
        )
        
        full_prompt = f"{system_prompt}\n\nUser: {user_input}\nJARVIS:"
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=full_prompt
        )
        jarvis_reply = response.text
        
        # Let the user know JARVIS is thinking/acting
        await safe_reply(update, jarvis_reply)

        # Simple parser for the model's 'actions'
        for line in jarvis_reply.split('\n'):
            if line.startswith("RUN_CMD:"):
                cmd = line.replace("RUN_CMD:", "").strip()
                try:
                    # Update local CWD if command contains 'cd '
                    # This is naive but helpful for single-line chains
                    # For deeper state, we rely on the LLM chaining with &&
                    process_output = subprocess.check_output(
                        cmd, 
                        shell=True, 
                        stderr=subprocess.STDOUT,
                        cwd=context.chat_data['cwd']
                    ).decode('utf-8')
                    
                    # If the command successfully changed directory in the shell, 
                    # we should try to track that. However, cd inside shell=True
                    # doesn't affect the parent. So we rely on the LLM to use absolute paths 
                    # or chain commands in one string.
                    
                    msg = f"**Execution Output, Sir:**\n\n```\n{process_output[:2000]}\n```"
                    await safe_reply(update, msg)
                except subprocess.CalledProcessError as e:
                    err_msg = f"Sir, the command failed with error:\n\n```\n{e.output.decode('utf-8')[:2000]}\n```"
                    await safe_reply(update, err_msg)
            
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





