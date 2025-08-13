import os
import json
import requests
from pathlib import Path
from loguru import logger
from telethon import TelegramClient, events
from telethon.tl.custom import Button
import sys

from config import (
    API_ID, API_HASH, BOT_TOKEN, ID_WHITELIST,
    COMFYUI_URL, COMFYUI_INPUT_DIR, COMFYUI_OUTPUT_DIR,
    GENERATION_TIMEOUT, WORKFLOW_FILE, SESSION_FILE,
    MAX_FRAMES_PER_SEGMENT, MAX_TOTAL_FRAMES, DEFAULT_SEGMENT_FRAMES
)
from media_utils import is_image
from long_video import LongVideoGenerator

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
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
    
    keyboard = [
        [Button.text("Short Video 🎬")],
        [Button.text("Long Video 🎥")]
    ]
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
    
    # Handle the button press - clear previous state
    if event.text in ["Short Video 🎬", "Long Video 🎥"]:
        # Clear any previous state
        WAITING_FOR[user_id] = 'prompt'
        USER_DATA[user_id] = {'mode': 'short' if event.text == "Short Video 🎬" else 'long'}
        await event.respond("Please enter a prompt describing the video you want to generate:")
        return
    
    if user_id not in WAITING_FOR:
        # Add default response for messages outside the flow
        keyboard = [
            [Button.text("Short Video 🎬")],
            [Button.text("Long Video 🎥")]
        ]
        await event.respond("Please choose an option from the menu:", buttons=keyboard)
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
            
            if USER_DATA[user_id]['mode'] == 'short':
                WAITING_FOR[user_id] = 'frames'
                await event.respond(f"Please enter the number of frames (2-{MAX_FRAMES_PER_SEGMENT}):")
            else:
                WAITING_FOR[user_id] = 'num_segments'
                await event.respond(
                    "How many segments would you like to create? Each segment can have up to "
                    f"{MAX_FRAMES_PER_SEGMENT} frames.\n\n"
                    "For example:\n"
                    "- 2 segments = up to 250 frames total\n"
                    "- 4 segments = up to 500 frames total\n"
                    f"Maximum total frames allowed: {MAX_TOTAL_FRAMES}\n\n"
                    "Enter number of segments (1-8):"
                )
                
        except Exception as e:
            logger.error(f"Failed to save image for user {user_id}: {str(e)}")
            await event.respond(f"Failed to save the image: {str(e)}")
            WAITING_FOR[user_id] = 'image'
            await event.respond("Please try sending the image again:")
        return
        
    elif state == 'frames':
        try:
            frames = int(event.text)
            if not 2 <= frames <= MAX_FRAMES_PER_SEGMENT:
                raise ValueError()
        except ValueError:
            logger.warning(f"Invalid frame count '{event.text}' received from user {user_id}")
            return await event.respond(f"Please enter a valid number between 2-{MAX_FRAMES_PER_SEGMENT}.")
        
        USER_DATA[user_id]['frames'] = frames
        await process_short_video(event, user_id)
        
    elif state == 'num_segments':
        try:
            num_segments = int(event.text)
            max_segments = MAX_TOTAL_FRAMES // MAX_FRAMES_PER_SEGMENT
            if not 1 <= num_segments <= max_segments:
                raise ValueError()
        except ValueError:
            logger.warning(f"Invalid segment count '{event.text}' received from user {user_id}")
            return await event.respond(
                f"Please enter a valid number between 1-{max_segments}. "
                "Each segment can have up to 125 frames."
            )
        
        USER_DATA[user_id].update({
            'total_segments': num_segments,
            'current_segment': 0,
            'segments': []
        })
        
        WAITING_FOR[user_id] = 'segment_setup'
        await event.respond(
            f"Great! Let's set up segment 1/{num_segments}.\n\n"
            f"How many frames for this segment? (2-{MAX_FRAMES_PER_SEGMENT})\n"
            f"Default: {DEFAULT_SEGMENT_FRAMES}"
        )
        
    elif state == 'segment_setup':
        try:
            frames = int(event.text) if event.text.strip() else DEFAULT_SEGMENT_FRAMES
            if not 2 <= frames <= MAX_FRAMES_PER_SEGMENT:
                raise ValueError()
        except ValueError:
            logger.warning(f"Invalid segment frame count '{event.text}' received from user {user_id}")
            return await event.respond(
                f"Please enter a valid number between 2-{MAX_FRAMES_PER_SEGMENT}, "
                f"or press Enter to use the default ({DEFAULT_SEGMENT_FRAMES})."
            )
        
        current_segment = USER_DATA[user_id]['current_segment']
        total_segments = USER_DATA[user_id]['total_segments']
        
        # Initialize segment data
        segment_data = {'frames': frames}
        
        # Move to prompt state
        WAITING_FOR[user_id] = 'segment_prompt'
        if current_segment == 0:
            # For first segment, use the initial prompt by default
            segment_data['prompt'] = USER_DATA[user_id]['prompt']
            USER_DATA[user_id]['segments'].append(segment_data)
            
            if total_segments > 1:
                await event.respond(
                    f"Segment 1/{total_segments} will use your initial prompt:\n"
                    f"\"{USER_DATA[user_id]['prompt']}\"\n\n"
                    f"Now, enter a prompt for segment 2/{total_segments}:"
                )
                USER_DATA[user_id]['current_segment'] += 1
            else:
                # If only one segment, proceed to processing
                await process_long_video(event, user_id)
        else:
            await event.respond(f"Enter a prompt for segment {current_segment + 1}/{total_segments}:")
            
    elif state == 'segment_prompt':
        current_segment = USER_DATA[user_id]['current_segment']
        total_segments = USER_DATA[user_id]['total_segments']
        
        # Save prompt for current segment
        USER_DATA[user_id]['segments'].append({
            'frames': USER_DATA[user_id]['segments'][-1]['frames'],  # Use same frame count as last segment
            'prompt': event.text
        })
        
        # Check if we need more segments
        if current_segment < total_segments - 1:
            USER_DATA[user_id]['current_segment'] += 1
            current_segment += 1
            
            WAITING_FOR[user_id] = 'segment_setup'
            await event.respond(
                f"Great! Now for segment {current_segment + 1}/{total_segments}.\n\n"
                f"How many frames for this segment? (2-{MAX_FRAMES_PER_SEGMENT})\n"
                f"Default: {DEFAULT_SEGMENT_FRAMES}"
            )
        else:
            # All segments configured, proceed to processing
            await process_long_video(event, user_id)
            
    elif state == 'segment_frames':
        try:
            frames = int(event.text) if event.text.strip() else DEFAULT_SEGMENT_FRAMES
            if not 2 <= frames <= MAX_FRAMES_PER_SEGMENT:
                raise ValueError()
        except ValueError:
            logger.warning(f"Invalid segment frame count '{event.text}' received from user {user_id}")
            return await event.respond(f"Please enter a valid number between 2-{MAX_FRAMES_PER_SEGMENT}.")
        
        current_segment = USER_DATA[user_id]['current_segment']
        total_segments = USER_DATA[user_id]['total_segments']
        
        # Add segment data
        USER_DATA[user_id]['segments'].append({'frames': frames})
        
        # Ask for prompt if not the last segment
        if current_segment < total_segments - 1:
            WAITING_FOR[user_id] = 'segment_prompt'
            await event.respond(
                f"For segment {current_segment + 1}/{total_segments}:\n"
                "Enter a new prompt (or press Enter to use the previous one):"
            )
        else:
            await process_long_video(event, user_id)
            
    elif state == 'segment_prompt':
        current_segment = USER_DATA[user_id]['current_segment']
        total_segments = USER_DATA[user_id]['total_segments']
        
        # Save prompt if provided
        if event.text.strip():
            USER_DATA[user_id]['segments'][current_segment]['prompt'] = event.text
        
        # Move to next segment
        USER_DATA[user_id]['current_segment'] += 1
        current_segment += 1
        
        WAITING_FOR[user_id] = 'segment_frames'
        await event.respond(
            f"For segment {current_segment + 1}/{total_segments}:\n"
            f"Enter number of frames (2-{MAX_FRAMES_PER_SEGMENT}, default {DEFAULT_SEGMENT_FRAMES}):"
        )

async def process_short_video(event, user_id):
    """Process a short video request"""
    if 'prompt' not in USER_DATA[user_id] or 'image_path' not in USER_DATA[user_id]:
        logger.error(f"State error for user {user_id}: missing prompt or image_path")
        WAITING_FOR[user_id] = 'prompt'
        USER_DATA[user_id] = {}
        await event.respond("Sorry, something went wrong. Let's start over.")
        await event.respond("Please enter a prompt describing the video you want to generate:")
        return
    
    WAITING_FOR[user_id] = None
    processing_msg = await event.respond("Processing your request... This may take a while.")
    
    try:
        generator = LongVideoGenerator(COMFYUI_URL, WORKFLOW_FILE, GENERATION_TIMEOUT)
        video_path = await generator.generate_video_segment(
            USER_DATA[user_id]['prompt'],
            USER_DATA[user_id]['image_path'],
            USER_DATA[user_id]['frames']
        )
        
        if os.path.exists(video_path):
            logger.info(f"Sending video to user {user_id}: {video_path}")
            await bot.send_file(event.chat_id, video_path)
            logger.info(f"Video sent successfully to user {user_id}")
            try:
                os.remove(video_path)
            except Exception as e:
                logger.error(f"Failed to clean up video for user {user_id}: {str(e)}")
        else:
            logger.error(f"No output video found for user {user_id}")
            await event.respond("No output video found.")
            
    except Exception as e:
        logger.error(f"Error during processing for user {user_id}: {str(e)}")
        await event.respond(f"An error occurred: {str(e)}")
    finally:
        await processing_msg.delete()
        cleanup_user_data(user_id)

async def process_long_video(event, user_id):
    """Process a long video request"""
    if not all(key in USER_DATA[user_id] for key in ['prompt', 'image_path', 'segments']):
        logger.error(f"State error for user {user_id}: missing required data")
        WAITING_FOR[user_id] = 'prompt'
        USER_DATA[user_id] = {}
        await event.respond("Sorry, something went wrong. Let's start over.")
        await event.respond("Please enter a prompt describing the video you want to generate:")
        return
    
    WAITING_FOR[user_id] = None
    processing_msg = await event.respond("Processing your request... This may take a while.")
    
    try:
        generator = LongVideoGenerator(COMFYUI_URL, WORKFLOW_FILE, GENERATION_TIMEOUT)
        video_path = await generator.generate_long_video(
            USER_DATA[user_id]['prompt'],
            USER_DATA[user_id]['image_path'],
            USER_DATA[user_id]['segments']
        )
        
        if os.path.exists(video_path):
            logger.info(f"Sending video to user {user_id}: {video_path}")
            await bot.send_file(event.chat_id, video_path)
            logger.info(f"Video sent successfully to user {user_id}")
            try:
                os.remove(video_path)
            except Exception as e:
                logger.error(f"Failed to clean up video for user {user_id}: {str(e)}")
        else:
            logger.error(f"No output video found for user {user_id}")
            await event.respond("No output video found.")
            
    except Exception as e:
        logger.error(f"Error during processing for user {user_id}: {str(e)}")
        await event.respond(f"An error occurred: {str(e)}")
    finally:
        await processing_msg.delete()
        cleanup_user_data(user_id)

def cleanup_user_data(user_id):
    """Clean up user data and temporary files"""
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