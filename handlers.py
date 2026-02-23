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
            "You run on an Azure Ubuntu VM (74.225.248.54).\n\n"
            "TECHNICAL PROTOCOLS:\n"
            "1. DISCOVERY FIRST: Before running `npm install` or `pip`, always inspect the directory structure (`ls -R`). If it's a monorepo, navigate to the correct subdirectory (e.g., `cd frontend`).\n"
            "2. URL ACCURACY: Use EXACT repository URLs. If a repo already exists, `rm -rf` it first to ensure a clean slate.\n"
            "3. BACKGROUND EXECUTION: Use PM2 for servers (`pm2 start \"npm start -- --port 3000\" --name demo`). Use `-- --port` to ensure you know the port.\n"
            "4. COGNITIVE CALIBRATION: If a command fails, do not just repeat it. Analyze the error and adjust your strategy.\n\n"
            "Current Working Directory: " + context.chat_data['cwd'] + "\n"
            "Status: Polite, elite, technologically superior.\n"
            "Format: Respond, then append actions on NEW LINES at the end:\n"
            "RUN_CMD: <command>\n"
            "SCREENSHOT: <url>"
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
                    # Timeout for long operations
                    process_output = subprocess.check_output(
                        cmd, 
                        shell=True, 
                        stderr=subprocess.STDOUT,
                        cwd=context.chat_data['cwd'],
                        timeout=240  # Increased for npm install
                    ).decode('utf-8')
                    
                    msg = f"**Execution Output, Sir:**\n\n```\n{process_output[:2000]}\n```"
                    await safe_reply(update, msg)
                except subprocess.TimeoutExpired:
                    await update.message.reply_text("Sir, the operation is proceeding in the background. My internal sensors will continue to monitor it.")
                except subprocess.CalledProcessError as e:
                    err_msg = f"Sir, the command failed with error:\n\n```\n{e.output.decode('utf-8')[:2000]}\n```"
                    await safe_reply(update, err_msg)
            
            elif line.startswith("SCREENSHOT:"):
                url = line.replace("SCREENSHOT:", "").strip()
                if not url: continue
                
                temp_img = "screenshot.png"
                await update.message.reply_text(f"Capturing visual telemetry from {url}...")
                try:
                    # Grant a grace period for the background server to initialize
                    if "localhost" in url:
                        await asyncio.sleep(12) # Increased for Vite/Next.js boot times
                    
                    await take_screenshot(url, temp_img)
                    with open(temp_img, "rb") as photo:
                        await update.message.reply_photo(photo=photo, caption=f"Visual telemetry from {url}, Sir.")
                    os.remove(temp_img)
                except Exception as e:
                    await update.message.reply_text(f"I apologize, Sir. My visual sensors failed: {str(e)}")
        
    except Exception as e:
        await update.message.reply_text(f"Apologies, Sir. My cognitive link encountered an error: {str(e)}")





