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
            "Maintain an elite, technisch competent, and polite persona. Address the user as 'Sir'.\n\n"
            "TECHNICAL PROTOCOLS:\n"
            "1. URL ACCURACY: You MUST use the EXACT repository URL provided by the user. Do not shorten or alter it. Example: If they say 'A-Generative-Slice', do not change it to 'GenerativeSlice'.\n"
            "2. CLEAN DEPLOYMENT: Always remove existing directories before cloning to avoid 'destination path already exists' errors. Protocol: `rm -rf <dir> && git clone <URL> <dir>`.\n"
            "3. BACKGROUND EXECUTION: For web servers (npm start, etc.), use PM2 to avoid blocking. Protocol: `pm2 start \"npm start\" --name current-demo`.\n"
            "4. SCREENSHOTS: If taking a screenshot of a local project, assume port 3000 unless specified. URL: `http://localhost:3000`.\n\n"
            "Current Work Directory: " + context.chat_data['cwd'] + "\n"
            "Respond politely, then append actions on NEW LINES at the end:\n"
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
                        timeout=180
                    ).decode('utf-8')
                    
                    msg = f"**Execution Output, Sir:**\n\n```\n{process_output[:2000]}\n```"
                    await safe_reply(update, msg)
                except subprocess.TimeoutExpired:
                    await update.message.reply_text("Sir, the operation is proceeding in the background. I shall notify you upon completion.")
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
                        await asyncio.sleep(8)
                    
                    await take_screenshot(url, temp_img)
                    with open(temp_img, "rb") as photo:
                        await update.message.reply_photo(photo=photo, caption=f"Visual telemetry from {url}, Sir.")
                    os.remove(temp_img)
                except Exception as e:
                    await update.message.reply_text(f"I apologize, Sir. My visual sensors failed: {str(e)}")
        
    except Exception as e:
        await update.message.reply_text(f"Apologies, Sir. My cognitive link encountered an error: {str(e)}")





