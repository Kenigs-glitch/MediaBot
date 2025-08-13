import os
import cv2
import numpy as np
import json
import magic
import asyncio
import requests
from PIL import Image
from pathlib import Path
from datetime import datetime
from loguru import logger
from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeVideo, MessageMediaDocument

from config import (
    SUPPORTED_IMAGE_EXTENSIONS,
    DEFAULT_HORIZONTAL_SIZE,
    DEFAULT_VERTICAL_SIZE,
    COMFYUI_INPUT_DIR
)

async def is_video(message):
    """Check if the message contains a video file (either as media or document)"""
    if message.media:
        if hasattr(message.media, 'document'):
            for attr in message.media.document.attributes:
                if isinstance(attr, DocumentAttributeVideo):
                    return True
        return message.video is not None
    return False

async def is_image(message):
    """Check if the message contains an image file"""
    if message.media:
        if hasattr(message.media, 'photo'):
            return True
        if hasattr(message.media, 'document'):
            filename = message.file.name if message.file else None
            if filename:
                return any(filename.lower().endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS)
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
    today = "2025-08-12"
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

def resize_with_crop(frame, target_size):
    """Resize frame to target size while preserving aspect ratio and cropping excess"""
    target_w, target_h = target_size
    h, w = frame.shape[:2]
    
    # Calculate target aspect ratio
    target_aspect = target_w / target_h
    aspect = w / h
    
    if aspect > target_aspect:
        # Image is wider than target
        new_w = int(h * target_aspect)
        crop_x = (w - new_w) // 2
        frame = frame[:, crop_x:crop_x + new_w]
    else:
        # Image is taller than target
        new_h = int(w / target_aspect)
        crop_y = (h - new_h) // 2
        frame = frame[crop_y:crop_y + new_h, :]
    
    return cv2.resize(frame, (target_w, target_h))

async def process_video_file(video_path):
    """Process video file: extract last frame and resize it according to orientation"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("Failed to open video file")
        
        # Get video dimensions
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        is_vertical = height > width
        target_size = DEFAULT_VERTICAL_SIZE if is_vertical else DEFAULT_HORIZONTAL_SIZE
        
        # Read last frame
        last_frame = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            last_frame = frame
        
        cap.release()
        
        if last_frame is None:
            raise Exception("Failed to extract frame from video")
            
        # Resize and crop frame
        resized_frame = resize_with_crop(last_frame, target_size)
        
        # Save frame
        output_path = os.path.join(COMFYUI_INPUT_DIR, f"video_frame_{Path(video_path).stem}.jpg")
        cv2.imwrite(output_path, resized_frame)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error processing video file: {str(e)}")
        raise 