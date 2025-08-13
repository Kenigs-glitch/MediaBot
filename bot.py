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
from media_utils import (
    is_image, is_video, process_video_file,
    process_image_to_video
)
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

async def show_initial_menu(event):
    """Show the initial menu with video generation options"""
    keyboard = [
        [Button.text("Short Video 🎬")],
        [Button.text("Long Video 🎥")]
    ]
    return await event.respond("Choose an option:", buttons=keyboard)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command"""
    user = await event.get_sender()
    logger.info(f"Start command received from user {user.id} (@{user.username})")
    
    if not is_authorized(event.sender_id):
        logger.warning(f"Unauthorized access attempt from user {user.id} (@{user.username})")
        return await event.respond("You are not authorized to use this bot.")
    
    await show_initial_menu(event)

def parse_multi_prompt_message(message_text):
    """Parse a message with multiple prompts and frame numbers.
    Format: Prompt1\nFrames_N1\nPrompt2\nFrames_N2 and so on
    Returns: List of tuples (prompt, frames) or None if invalid format
    """
    try:
        # Split into lines and remove empty lines
        lines = [line.strip() for line in message_text.split('\n') if line.strip()]
        
        # Must have even number of lines (prompt + frames pairs)
        if len(lines) % 2 != 0 or len(lines) == 0 or len(lines) > 100:  # 50 pairs max
            return None
            
        segments = []
        total_frames = 0
        
        for i in range(0, len(lines), 2):
            prompt = lines[i]
            try:
                frames = int(lines[i + 1])
                # Validate per-segment frame count
                if not 2 <= frames <= MAX_FRAMES_PER_SEGMENT:
                    logger.warning(f"Invalid frame count {frames} - must be between 2 and {MAX_FRAMES_PER_SEGMENT}")
                    return None
                    
                total_frames += frames
                # Validate total frames
                if total_frames > MAX_TOTAL_FRAMES:
                    logger.warning(f"Total frames {total_frames} exceeds maximum {MAX_TOTAL_FRAMES}")
                    return None
                    
            except ValueError:
                logger.warning("Invalid frame number format")
                return None
                
            segments.append((prompt, frames))
            
        return segments
    except Exception as e:
        logger.error(f"Error parsing multi-prompt message: {str(e)}")
        return None

@bot.on(events.NewMessage())
async def message_handler(event):
    """Handle all other messages"""
    user = await event.get_sender()
    user_id = user.id
    
    if not is_authorized(user_id):
        logger.warning(f"Unauthorized message from user {user_id} (@{user.username})")
        return
    
    logger.info(f"Message received from user {user_id} (@{user.username}): {event.text[:50]}...")
    
    # Handle media with caption (image or video)
    if event.message.media and event.message.message:
        is_img = await is_image(event.message)
        is_vid = await is_video(event.message)
        
        if not (is_img or is_vid):
            return await event.respond("Please send a valid image or video file.")
            
        # Try to parse multi-prompt format
        segments = parse_multi_prompt_message(event.message.message)
        if segments:
            # Download media
            try:
                temp_path = os.path.join(COMFYUI_INPUT_DIR, f"input_{user_id}_temp")
                download_path = await event.message.download_media(temp_path)
                
                if not download_path:
                    raise Exception("Failed to download media")
                
                # If it's a video, process it to extract the last frame
                if is_vid:
                    logger.info(f"Processing video from user {user_id}")
                    image_path = await process_video_file(download_path)
                    # Clean up temp video file
                    os.remove(download_path)
                else:
                    image_path = download_path
                
                logger.info(f"Saved media from user {user_id} to: {image_path}")
                
                # Initialize data for long video generation
                USER_DATA[user_id] = {
                    'mode': 'long',
                    'image_path': image_path,
                    'prompt': segments[0][0],  # Use first prompt as default
                    'segments': [
                        {'prompt': prompt, 'frames': frames}
                        for prompt, frames in segments
                    ]
                }
                
                # Process the video
                await process_long_video(event, user_id)
                return
                
            except Exception as e:
                logger.error(f"Error processing multi-prompt request for user {user_id}: {str(e)}")
                await event.respond(f"An error occurred: {str(e)}")
                await show_initial_menu(event)
                if 'download_path' in locals() and os.path.exists(download_path):
                    os.remove(download_path)
                return
    
    # Handle the button press - clear previous state
    if event.text in ["Short Video 🎬", "Long Video 🎥"]:
        # Clear any previous state
        WAITING_FOR[user_id] = 'prompt'
        USER_DATA[user_id] = {'mode': 'short' if event.text == "Short Video 🎬" else 'long'}
        await event.respond("Please enter a prompt describing the video you want to generate:")
        return
    
    if user_id not in WAITING_FOR:
        # Add default response for messages outside the flow
        await show_initial_menu(event)
        return
    
    state = WAITING_FOR[user_id]
    logger.info(f"Processing state '{state}' for user {user_id} (@{user.username})")
    
    if state == 'prompt':
        USER_DATA[user_id]['prompt'] = event.text
        logger.info(f"Saved prompt for user {user_id}: {event.text}")
        WAITING_FOR[user_id] = 'media'
        await event.respond("Please send an image or video:")
        return
        
    elif state == 'media':
        is_img = await is_image(event.message)
        is_vid = await is_video(event.message)
        
        if not (is_img or is_vid):
            logger.warning(f"Invalid media file received from user {user_id}")
            return await event.respond("Please send a valid image or video file.")
        
        # Download media
        try:
            temp_path = os.path.join(COMFYUI_INPUT_DIR, f"input_{user_id}_temp")
            download_path = await event.message.download_media(temp_path)
            
            if not download_path:
                raise Exception("Failed to download media")
            
            # If it's a video, process it to extract the last frame
            if is_vid:
                logger.info(f"Processing video from user {user_id}")
                image_path = await process_video_file(download_path)
                # Clean up temp video file
                os.remove(download_path)
            else:
                image_path = download_path
            
            logger.info(f"Saved media from user {user_id} to: {image_path}")
            USER_DATA[user_id]['image_path'] = image_path
            
            if USER_DATA[user_id]['mode'] == 'short':
                WAITING_FOR[user_id] = 'frames'
                await event.respond(f"Please enter the number of frames (2-{MAX_FRAMES_PER_SEGMENT}):")
            else:
                # Initialize long video data
                USER_DATA[user_id].update({
                    'segments': [],
                    'total_frames': 0
                })
                WAITING_FOR[user_id] = 'segment_setup'
                await event.respond(
                    "Let's create your video segment by segment.\n\n"
                    f"How many frames for segment 1? (2-{MAX_FRAMES_PER_SEGMENT})\n"
                    f"Default: {DEFAULT_SEGMENT_FRAMES}"
                )
                
        except Exception as e:
            logger.error(f"Error processing media for user {user_id}: {str(e)}")
            await event.respond(f"An error occurred: {str(e)}")
            if 'download_path' in locals() and os.path.exists(download_path):
                os.remove(download_path)
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
            
    elif state == 'segment_setup':
        try:
            frames = int(event.text) if event.text.strip() else DEFAULT_SEGMENT_FRAMES
            if not 2 <= frames <= MAX_FRAMES_PER_SEGMENT:
                raise ValueError()
            
            # Check if adding these frames would exceed the maximum
            new_total = USER_DATA[user_id]['total_frames'] + frames
            if new_total > MAX_TOTAL_FRAMES:
                return await event.respond(
                    f"Adding {frames} frames would exceed the maximum total of {MAX_TOTAL_FRAMES} frames.\n"
                    f"You currently have {USER_DATA[user_id]['total_frames']} frames.\n"
                    f"You can add up to {MAX_TOTAL_FRAMES - USER_DATA[user_id]['total_frames']} more frames.\n\n"
                    "Please enter a smaller number:"
                )
        except ValueError:
            logger.warning(f"Invalid segment frame count '{event.text}' received from user {user_id}")
            return await event.respond(
                f"Please enter a valid number between 2-{MAX_FRAMES_PER_SEGMENT}, "
                f"or press Enter to use the default ({DEFAULT_SEGMENT_FRAMES})."
            )
        
        # Store frames temporarily
        USER_DATA[user_id]['temp_frames'] = frames
        
        # Move to prompt state
        WAITING_FOR[user_id] = 'segment_prompt'
        if not USER_DATA[user_id]['segments']:  # First segment
            # Use initial prompt for first segment
            USER_DATA[user_id]['segments'].append({
                'frames': frames,
                'prompt': USER_DATA[user_id]['prompt']
            })
            USER_DATA[user_id]['total_frames'] = frames
            
            # Ask if user wants to add another segment
            keyboard = [
                [Button.text("✅ Process Video")],
                [Button.text("➕ Add Another Segment")]
            ]
            await event.respond(
                f"Segment 1 configured with {frames} frames.\n"
                f"Total frames so far: {frames}\n\n"
                "Would you like to add another segment or process the video?",
                buttons=keyboard
            )
        else:
            await event.respond(f"Enter a prompt for segment {len(USER_DATA[user_id]['segments']) + 1}:")
            
    elif state == 'segment_prompt':
        if event.text == "✅ Process Video":
            await process_long_video(event, user_id)
            return
        elif event.text == "➕ Add Another Segment":
            WAITING_FOR[user_id] = 'segment_setup'
            segment_num = len(USER_DATA[user_id]['segments']) + 1
            frames_left = MAX_TOTAL_FRAMES - USER_DATA[user_id]['total_frames']
            max_frames = min(MAX_FRAMES_PER_SEGMENT, frames_left)
            
            await event.respond(
                f"How many frames for segment {segment_num}? (2-{max_frames})\n"
                f"Default: {min(DEFAULT_SEGMENT_FRAMES, max_frames)}\n\n"
                f"Total frames so far: {USER_DATA[user_id]['total_frames']}"
            )
            return
        
        # Regular prompt handling
        segment_num = len(USER_DATA[user_id]['segments']) + 1
        frames = USER_DATA[user_id]['temp_frames']
        
        # Add the new segment
        USER_DATA[user_id]['segments'].append({
            'frames': frames,
            'prompt': event.text
        })
        USER_DATA[user_id]['total_frames'] += frames
        
        # Ask if user wants to add another segment
        frames_left = MAX_TOTAL_FRAMES - USER_DATA[user_id]['total_frames']
        keyboard = [
            [Button.text("✅ Process Video")],
            [Button.text("➕ Add Another Segment")] if frames_left >= 2 else []
        ]
        
        await event.respond(
            f"Segment {segment_num} configured with {frames} frames.\n"
            f"Total frames so far: {USER_DATA[user_id]['total_frames']}\n"
            f"Frames remaining: {frames_left}\n\n"
            "Would you like to add another segment or process the video?",
            buttons=keyboard
        )
            
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
    try:
        # Get user data
        data = USER_DATA[user_id]
        prompt = data['prompt']
        image_path = data['image_path']
        n_frames = data['frames']
        
        # Process the video
        await event.respond("Processing your video... This may take a while.")
        await process_image_to_video(prompt, image_path, n_frames, COMFYUI_URL, WORKFLOW_FILE)
        
        # Clean up
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # Reset state
        WAITING_FOR.pop(user_id, None)
        USER_DATA.pop(user_id, None)
        
        # Show success message and return to initial menu
        await event.respond("Video processing completed!")
        await show_initial_menu(event)
        
    except Exception as e:
        logger.error(f"Error processing video for user {user_id}: {str(e)}")
        await event.respond(f"An error occurred while processing your video: {str(e)}")
        await show_initial_menu(event)

async def process_long_video(event, user_id):
    """Process a long video request"""
    try:
        data = USER_DATA[user_id]
        generator = LongVideoGenerator(
            image_path=data['image_path'],
            segments=data['segments'],
            default_prompt=data['prompt']
        )
        
        await event.respond("Processing your video... This may take a while.")
        await generator.generate()
        
        # Clean up
        if os.path.exists(data['image_path']):
            os.remove(data['image_path'])
        
        # Reset state
        WAITING_FOR.pop(user_id, None)
        USER_DATA.pop(user_id, None)
        
        # Show success message and return to initial menu
        await event.respond("Video processing completed!")
        await show_initial_menu(event)
        
    except Exception as e:
        logger.error(f"Error processing long video for user {user_id}: {str(e)}")
        await event.respond(f"An error occurred while processing your video: {str(e)}")
        await show_initial_menu(event)

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