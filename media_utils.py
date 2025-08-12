import os
import json
import magic
import asyncio
import requests
from PIL import Image
from pathlib import Path
from telethon.tl.types import DocumentAttributeFilename

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
            if filename and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
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
        return (720, 1280) if is_vertical else (1280, 720)

async def process_image_to_video(prompt, image_path, n_frames, comfyui_url, workflow_file):
    """Process image using ComfyUI workflow"""
    width, height = await get_image_dimensions(image_path)
    
    # Load workflow template
    with open(workflow_file, 'r') as f:
        workflow = json.load(f)
    
    # Update workflow parameters
    def update_workflow_params(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and "doing gymnastics" in value:
                    obj[key] = prompt
                elif value in [720, "720"]:
                    obj[key] = height
                elif value in [1280, "1280"]:
                    obj[key] = width
                elif value in [101, "101"]:
                    obj[key] = n_frames
                elif isinstance(value, str) and value.endswith(('.png', '.jpg', '.jpeg')):
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
    start_time = asyncio.get_event_loop().time()
    while True:
        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError("Generation timed out")
        
        history_response = requests.get(f"{comfyui_url}/history/{prompt_id}")
        if history_response.status_code == 200:
            history_data = history_response.json()
            if prompt_id in history_data:
                return True
        
        await asyncio.sleep(3)

def get_latest_video(output_dir):
    """Get the latest video file from the output directory"""
    output_dir = Path(output_dir)
    video_files = list(output_dir.glob('*.mp4'))
    if video_files:
        return max(video_files, key=lambda x: x.stat().st_mtime)
    return None 