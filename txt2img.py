import json
import requests
import asyncio
import os
from pathlib import Path
from loguru import logger
from PIL import Image

# Configuration
DREAMSHAPER_WORKFLOW_FILE = "dreamshaper_txt_to_img.json"
DEFAULT_HORIZONTAL_SIZE = (1280, 720)  # width, height for horizontal images
DEFAULT_VERTICAL_SIZE = (720, 1280)  # width, height for vertical images

def determine_image_size(prompt):
    """Determine image size based on prompt keywords indicating orientation"""
    prompt_lower = prompt.lower()
    
    # Keywords that suggest vertical orientation
    vertical_keywords = [
        'portrait', 'vertical', 'tall', 'standing', 'person', 'human', 'figure',
        'full body', 'full-body', 'character', 'portrait shot', 'close up',
        'face', 'head', 'bust', 'torso', 'selfie', 'profile'
    ]
    
    # Keywords that suggest horizontal orientation
    horizontal_keywords = [
        'landscape', 'horizontal', 'wide', 'panorama', 'scenery', 'nature',
        'cityscape', 'street', 'road', 'beach', 'mountain', 'forest',
        'group', 'crowd', 'scene', 'environment', 'background', 'setting'
    ]
    
    # Count matches
    vertical_matches = sum(1 for keyword in vertical_keywords if keyword in prompt_lower)
    horizontal_matches = sum(1 for keyword in horizontal_keywords if keyword in prompt_lower)
    
    # Default to vertical for portraits, horizontal for landscapes
    if vertical_matches > horizontal_matches:
        return DEFAULT_VERTICAL_SIZE
    elif horizontal_matches > vertical_matches:
        return DEFAULT_HORIZONTAL_SIZE
    else:
        # Default to vertical for ambiguous cases
        return DEFAULT_VERTICAL_SIZE

async def process_text_to_image(prompt, comfyui_url, workflow_file=DREAMSHAPER_WORKFLOW_FILE):
    """Process text-to-image generation using DreamShaper workflow"""
    target_width, target_height = determine_image_size(prompt)
    
    # Load workflow template
    with open(workflow_file, 'r') as f:
        workflow = json.load(f)
    
    # Update workflow parameters
    def update_workflow_params(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if value == "cinematic film still, close up, a robot woman stands tall, half-human half machine, amongst an ancient Greek gallery of paintings and marble, religious symbolism, quantum wavetracing, high fashion editorial, glsl shaders, semiconductors and electronic computer hardware, amazing quality, wallpaper, analog film grain, perfect face skin ":
                    obj[key] = prompt
                elif value in [720, "720"]:
                    # Update width or height based on context
                    if key.lower().endswith('width'):
                        obj[key] = target_width
                    elif key.lower().endswith('height'):
                        obj[key] = target_height
                elif value in [1280, "1280"]:
                    # Update width or height based on context
                    if key.lower().endswith('width'):
                        obj[key] = target_width
                    elif key.lower().endswith('height'):
                        obj[key] = target_height
                else:
                    update_workflow_params(value)
        elif isinstance(obj, list):
            for item in obj:
                update_workflow_params(item)

    update_workflow_params(workflow)
    
    # Send to ComfyUI
    try:
        response = requests.post(f"{comfyui_url}/prompt",
                               json={"prompt": workflow, "client_id": "telegram_bot_txt2img"})
        
        if response.status_code == 200:
            return response.json()['prompt_id']
        
        raise Exception(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        raise Exception(f"Failed to process text-to-image: {str(e)}")

async def wait_for_image_generation(prompt_id, comfyui_url, timeout=600):
    """Wait for image generation to complete with timeout"""
    logger.info(f"Waiting for image generation to complete for prompt ID: {prompt_id}")
    start_time = asyncio.get_event_loop().time()
    
    while True:
        if asyncio.get_event_loop().time() - start_time > timeout:
            logger.error(f"Image generation timed out after {timeout} seconds")
            raise TimeoutError("Image generation timed out")
        
        history_response = requests.get(f"{comfyui_url}/history/{prompt_id}")
        if history_response.status_code == 200:
            history_data = history_response.json()
            logger.debug(f"History response for {prompt_id}: {history_data}")
            
            if prompt_id in history_data:
                logger.info(f"Image generation completed for prompt ID: {prompt_id}")
                return history_data[prompt_id]
        else:
            logger.warning(f"Failed to get history for prompt {prompt_id}: {history_response.status_code}")
        
        await asyncio.sleep(3)

def get_latest_image(output_dir):
    """Get the latest image file from the output directory"""
    logger.info(f"Looking for latest image in {output_dir}")
    output_dir = Path(output_dir)
    
    # First try date-based directory
    today = "2025-08-12"
    date_dir = output_dir / today
    
    image_files = []
    
    # Check date directory if it exists
    if date_dir.exists():
        logger.info(f"Checking date directory: {date_dir}")
        image_files.extend(list(date_dir.glob('*.png')))
        image_files.extend(list(date_dir.glob('*.jpg')))
        image_files.extend(list(date_dir.glob('*.jpeg')))
    
    # Also check root directory
    logger.info(f"Checking root directory: {output_dir}")
    image_files.extend(list(output_dir.glob('*.png')))
    image_files.extend(list(output_dir.glob('*.jpg')))
    image_files.extend(list(output_dir.glob('*.jpeg')))
    
    if image_files:
        latest_image = max(image_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Found latest image: {latest_image}")
        return latest_image
    
    logger.warning(f"No image files found in {output_dir}")
    return None

async def generate_image_from_text(prompt, comfyui_url, output_dir):
    """Complete text-to-image generation workflow"""
    try:
        logger.info(f"Starting text-to-image generation for prompt: {prompt}")
        
        # Process the text-to-image request
        prompt_id = await process_text_to_image(prompt, comfyui_url)
        logger.info(f"Text-to-image queued with prompt ID: {prompt_id}")
        
        # Wait for generation to complete
        await wait_for_image_generation(prompt_id, comfyui_url)
        
        # Get the generated image
        image_path = get_latest_image(output_dir)
        if not image_path:
            raise Exception("No generated image found")
        
        logger.info(f"Text-to-image generation completed: {image_path}")
        return image_path
        
    except Exception as e:
        logger.error(f"Error in text-to-image generation: {str(e)}")
        raise e 