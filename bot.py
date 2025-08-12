import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.custom import Button

from media_utils import (
    is_image,
    process_image_to_video,
    wait_for_generation,
    get_latest_video
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ID_WHITELIST = set(int(id_) for id_ in os.getenv('ID_WHITELIST', '').split(',') if id_)
COMFYUI_URL = os.getenv('COMFYUI_URL', 'http://192.168.100.11:8188')
COMFYUI_INPUT_DIR = os.getenv('COMFYUI_INPUT_DIR', '/storage/comfyui/input')
COMFYUI_OUTPUT_DIR = os.getenv('COMFYUI_OUTPUT_DIR', '/storage/comfyui/output')
GENERATION_TIMEOUT = int(os.getenv('GENERATION_TIMEOUT', 3600))
WORKFLOW_FILE = 'wan2.2_img_to_vid.json'

# Initialize bot
SESSION_FILE = os.path.join('sessions', 'bot.session')
os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
bot = TelegramClient(SESSION_FILE, API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Conversation states
WAITING_FOR = {}
USER_DATA = {}

def is_authorized(user_id):
    """Check if user is in whitelist"""
    return user_id in ID_WHITELIST

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command"""
    if not is_authorized(event.sender_id):
        return await event.respond("You are not authorized to use this bot.")
    
    keyboard = [[Button.text("Image to Video 🎬")]]
    await event.respond("Welcome! Choose an option:", buttons=keyboard)

@bot.on(events.NewMessage(pattern='Image to Video 🎬'))
async def img2vid_handler(event):
    """Handle Image to Video conversion request"""
    if not is_authorized(event.sender_id):
        return
    
    WAITING_FOR[event.sender_id] = 'prompt'
    USER_DATA[event.sender_id] = {}
    
    await event.respond("Please enter a prompt describing the video you want to generate:")

@bot.on(events.NewMessage())
async def message_handler(event):
    """Handle all other messages"""
    if not is_authorized(event.sender_id):
        return
    
    user_id = event.sender_id
    if user_id not in WAITING_FOR:
        return
    
    state = WAITING_FOR[user_id]
    logger.info(f"Processing state '{state}' for user {user_id}")
    
    if state == 'prompt':
        USER_DATA[user_id]['prompt'] = event.text
        logger.info(f"Saved prompt: {event.text}")
        WAITING_FOR[user_id] = 'image'
        await event.respond("Please send an image:")
        return
        
    elif state == 'image':
        if not await is_image(event.message):
            return await event.respond("Please send a valid image file.")
        
        # Download image
        try:
            download_path = os.path.join(COMFYUI_INPUT_DIR, f"input_{user_id}.jpg")
            await event.message.download_media(download_path)
            
            # Verify the file was actually downloaded
            if not os.path.exists(download_path):
                raise Exception("Failed to save the image")
            
            logger.info(f"Saved image to: {download_path}")
            USER_DATA[user_id]['image_path'] = download_path
            WAITING_FOR[user_id] = 'frames'
            await event.respond("Please enter the number of frames (2-125):")
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            await event.respond(f"Failed to save the image: {str(e)}")
            WAITING_FOR[user_id] = 'image'
            await event.respond("Please try sending the image again:")
        return
        
    elif state == 'frames':
        try:
            frames = int(event.text)
            if not 2 <= frames <= 125:
                raise ValueError()
        except ValueError:
            return await event.respond("Please enter a valid number between 2-125.")
        
        if 'prompt' not in USER_DATA[user_id] or 'image_path' not in USER_DATA[user_id]:
            # Something went wrong with the state, restart
            WAITING_FOR[user_id] = 'prompt'
            USER_DATA[user_id] = {}
            await event.respond("Sorry, something went wrong. Let's start over.")
            await event.respond("Please enter a prompt describing the video you want to generate:")
            return
            
        USER_DATA[user_id]['frames'] = frames
        WAITING_FOR[user_id] = None
        
        # Process the request
        processing_msg = await event.respond("Processing your request... This may take a while.")
        try:
            # Log current state
            logger.info(f"Processing request for user {user_id}:")
            logger.info(f"Prompt: {USER_DATA[user_id]['prompt']}")
            logger.info(f"Image: {USER_DATA[user_id]['image_path']}")
            logger.info(f"Frames: {frames}")
            
            # Verify ComfyUI connection first
            import requests
            try:
                health_check = requests.get(COMFYUI_URL, timeout=5)
                if health_check.status_code != 200:
                    raise Exception(f"ComfyUI server returned status {health_check.status_code}")
            except requests.exceptions.RequestException as e:
                raise Exception(f"Cannot connect to ComfyUI server: {str(e)}")
            
            prompt_id = await process_image_to_video(
                USER_DATA[user_id]['prompt'],
                USER_DATA[user_id]['image_path'],
                frames,
                COMFYUI_URL,
                WORKFLOW_FILE
            )
            
            logger.info(f"Got prompt ID: {prompt_id}")
            
            # Wait for completion
            await wait_for_generation(prompt_id, COMFYUI_URL, GENERATION_TIMEOUT)
            logger.info("Generation completed")
            
            # Find and send the output video
            latest_video = get_latest_video(COMFYUI_OUTPUT_DIR)
            if latest_video:
                logger.info(f"Sending video: {latest_video}")
                await bot.send_file(event.chat_id, str(latest_video))
                os.remove(str(latest_video))
                logger.info("Video sent and cleaned up")
            else:
                logger.error("No output video found")
                await event.respond("No output video found.")
            
        except Exception as e:
            logger.error(f"Error during processing: {str(e)}")
            await event.respond(f"An error occurred: {str(e)}")
        finally:
            await processing_msg.delete()
            if user_id in USER_DATA:
                try:
                    if 'image_path' in USER_DATA[user_id]:
                        os.remove(USER_DATA[user_id]['image_path'])
                        logger.info("Cleaned up input image")
                except:
                    pass
                del USER_DATA[user_id]

if __name__ == "__main__":
    # Ensure storage directories exist
    os.makedirs(COMFYUI_INPUT_DIR, exist_ok=True)
    os.makedirs(COMFYUI_OUTPUT_DIR, exist_ok=True)
    
    logger.info("Bot started...")
    bot.run_until_disconnected() 