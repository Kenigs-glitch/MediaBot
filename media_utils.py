import os
import json
import magic
import asyncio
import requests
from PIL import Image
from pathlib import Path
from datetime import datetime
from loguru import logger
from telethon.tl.types import DocumentAttributeFilename

from config import (
    SUPPORTED_IMAGE_EXTENSIONS,
    DEFAULT_HORIZONTAL_SIZE,
    DEFAULT_VERTICAL_SIZE
)

async def is_image(message):
    """Check if message contains an image"""
    if message.photo:
        return True
    if message.document:
        mime = magic.Magic(mime=True)
        try:
            filename = None
            for attr in message.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    filename = attr.file_name
                    break
            if filename and filename.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
                return True
            return message.document.mime_type and message.document.mime_type.startswith('image/')
        except Exception:
            return False
    return False

async def get_image_dimensions(file_path):
    """Get image dimensions and determine orientation"""
    with Image.open(file_path) as img:
        width, height = img.size
        is_vertical = height > width
        return DEFAULT_VERTICAL_SIZE if is_vertical else DEFAULT_HORIZONTAL_SIZE

async def process_image_to_video(prompt, image_path, n_frames, comfyui_url, workflow_file):
    """Process image using ComfyUI workflow"""
    target_width, target_height = await get_image_dimensions(image_path)
    
    # Load workflow template
    with open(workflow_file, 'r') as f:
        workflow = json.load(f)
    
    # Update workflow parameters
    def update_workflow_params(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if value == "a video of a beautiful blondie woman doing gymnastics on the floor":
                    obj[key] = prompt
                elif value in [720, "720", 1280, "1280"]:
                    # Update dimension based on whether it's width or height in the workflow
                    if key.lower().endswith('width'):
                        obj[key] = target_width
                    elif key.lower().endswith('height'):
                        obj[key] = target_height
                elif value in [101, "101"]:
                    obj[key] = n_frames
                elif isinstance(value, str) and value == "combined_opencv_last_frame.png":
                    obj[key] = os.path.basename(image_path)
                else:
                    update_workflow_params(value)
        elif isinstance(obj, list):
            for item in obj:
                update_workflow_params(item)

    update_workflow_params(workflow)
    
    # Send to ComfyUI
    try:
        response = requests.post(f"{comfyui_url}/prompt",
                               json={"prompt": workflow, "client_id": "telegram_bot"})
        
        if response.status_code == 200:
            return response.json()['prompt_id']
        
        raise Exception(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        raise Exception(f"Failed to process image: {str(e)}")

async def wait_for_generation(prompt_id, comfyui_url, timeout):
    """Wait for generation to complete with timeout"""
    logger.info(f"Waiting for generation to complete for prompt ID: {prompt_id}")
    start_time = asyncio.get_event_loop().time()
    
    while True:
        if asyncio.get_event_loop().time() - start_time > timeout:
            logger.error(f"Generation timed out after {timeout} seconds")
            raise TimeoutError("Generation timed out")
        
        history_response = requests.get(f"{comfyui_url}/history/{prompt_id}")
        if history_response.status_code == 200:
            history_data = history_response.json()
            logger.debug(f"History response for {prompt_id}: {history_data}")
            
            if prompt_id in history_data:
                logger.info(f"Generation completed for prompt ID: {prompt_id}")
                return True
        else:
            logger.warning(f"Failed to get history for prompt {prompt_id}: {history_response.status_code}")
        
        await asyncio.sleep(3)

def get_latest_video(output_dir):
    """Get the latest video file from the output directory"""
    logger.info(f"Looking for latest video in {output_dir}")
    output_dir = Path(output_dir)
    
    # First try date-based directory
    today = datetime.now().strftime('%Y-%m-%d')
    date_dir = output_dir / today
    
    video_files = []
    
    # Check date directory if it exists
    if date_dir.exists():
        logger.info(f"Checking date directory: {date_dir}")
        video_files.extend(list(date_dir.glob('*.mp4')))
    
    # Also check root directory
    logger.info(f"Checking root directory: {output_dir}")
    video_files.extend(list(output_dir.glob('*.mp4')))
    
    if video_files:
        latest_video = max(video_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Found latest video: {latest_video}")
        return latest_video
        
    logger.warning(f"No video files found in {output_dir} or {date_dir}")
    return None 