import os
import json
import requests
from pathlib import Path
from loguru import logger
from telethon import TelegramClient, events
from telethon.tl.custom import Button

from config import (
    API_ID, API_HASH, BOT_TOKEN, ID_WHITELIST,
    COMFYUI_URL, COMFYUI_INPUT_DIR, COMFYUI_OUTPUT_DIR,
    GENERATION_TIMEOUT, WORKFLOW_FILE, SESSION_FILE
)
from media_utils import (
    is_image,
    process_image_to_video,
    wait_for_generation,
    get_latest_video
)

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    lambda msg: print(msg),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

# Initialize bot
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
    user = await event.get_sender()
    logger.info(f"Start command received from user {user.id} (@{user.username})")
    
    if not is_authorized(event.sender_id):
        logger.warning(f"Unauthorized access attempt from user {user.id} (@{user.username})")
        return await event.respond("You are not authorized to use this bot.")
    
    keyboard = [[Button.text("Image to Video 🎬")]]
    await event.respond("Welcome! Choose an option:", buttons=keyboard)

@bot.on(events.NewMessage())
async def message_handler(event):
    """Handle all other messages"""
    user = await event.get_sender()
    user_id = user.id
    
    if not is_authorized(user_id):
        logger.warning(f"Unauthorized message from user {user_id} (@{user.username})")
        return
    
    logger.info(f"Message received from user {user_id} (@{user.username}): {event.text[:50]}...")
    
    # Handle the button press
    if event.text == "Image to Video 🎬":
        WAITING_FOR[user_id] = 'prompt'
        USER_DATA[user_id] = {}
        await event.respond("Please enter a prompt describing the video you want to generate:")
        return
    
    if user_id not in WAITING_FOR:
        return
    
    state = WAITING_FOR[user_id]
    logger.info(f"Processing state '{state}' for user {user_id} (@{user.username})")
    
    if state == 'prompt':
        USER_DATA[user_id]['prompt'] = event.text
        logger.info(f"Saved prompt for user {user_id}: {event.text}")
        WAITING_FOR[user_id] = 'image'
        await event.respond("Please send an image:")
        return
        
    elif state == 'image':
        if not await is_image(event.message):
            logger.warning(f"Invalid image file received from user {user_id}")
            return await event.respond("Please send a valid image file.")
        
        # Download image
        try:
            download_path = os.path.join(COMFYUI_INPUT_DIR, f"input_{user_id}.jpg")
            await event.message.download_media(download_path)
            
            # Verify the file was actually downloaded
            if not os.path.exists(download_path):
                raise Exception("Failed to save the image")
            
            logger.info(f"Saved image from user {user_id} to: {download_path}")
            USER_DATA[user_id]['image_path'] = download_path
            WAITING_FOR[user_id] = 'frames'
            await event.respond("Please enter the number of frames (2-125):")
        except Exception as e:
            logger.error(f"Failed to save image for user {user_id}: {str(e)}")
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
            logger.warning(f"Invalid frame count '{event.text}' received from user {user_id}")
            return await event.respond("Please enter a valid number between 2-125.")
        
        if 'prompt' not in USER_DATA[user_id] or 'image_path' not in USER_DATA[user_id]:
            # Something went wrong with the state, restart
            logger.error(f"State error for user {user_id}: missing prompt or image_path")
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
            logger.info(f"Processing request for user {user_id} (@{user.username}):")
            logger.info(f"Prompt: {USER_DATA[user_id]['prompt']}")
            logger.info(f"Image: {USER_DATA[user_id]['image_path']}")
            logger.info(f"Frames: {frames}")
            
            # Verify ComfyUI connection first
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
            
            logger.info(f"Got prompt ID for user {user_id}: {prompt_id}")
            
            # Wait for completion
            await wait_for_generation(prompt_id, COMFYUI_URL, GENERATION_TIMEOUT)
            logger.info(f"Generation completed for user {user_id}")
            
            # Find and send the output video
            latest_video = get_latest_video(COMFYUI_OUTPUT_DIR)
            if latest_video:
                logger.info(f"Sending video to user {user_id}: {latest_video}")
                await bot.send_file(event.chat_id, str(latest_video))
                logger.info(f"Video sent successfully to user {user_id}")
            else:
                logger.error(f"No output video found for user {user_id}")
                await event.respond("No output video found.")
            
        except Exception as e:
            logger.error(f"Error during processing for user {user_id}: {str(e)}")
            await event.respond(f"An error occurred: {str(e)}")
        finally:
            await processing_msg.delete()
            if user_id in USER_DATA:
                try:
                    if 'image_path' in USER_DATA[user_id]:
                        os.remove(USER_DATA[user_id]['image_path'])
                        logger.info(f"Cleaned up input image for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to clean up input image for user {user_id}: {str(e)}")
                del USER_DATA[user_id]

if __name__ == "__main__":
    logger.info("Bot started...")
    bot.run_until_disconnected() 