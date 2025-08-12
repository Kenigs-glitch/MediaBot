import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Bot Configuration
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ID_WHITELIST = set(int(id_) for id_ in os.getenv('ID_WHITELIST', '').split(',') if id_)

# ComfyUI Configuration
COMFYUI_URL = os.getenv('COMFYUI_URL', 'http://192.168.100.11:8188')
COMFYUI_INPUT_DIR = os.getenv('COMFYUI_INPUT_DIR', '/storage/comfyui/input')
COMFYUI_OUTPUT_DIR = os.getenv('COMFYUI_OUTPUT_DIR', '/storage/comfyui/output')
GENERATION_TIMEOUT = int(os.getenv('GENERATION_TIMEOUT', 3600))

# Workflow Configuration
WORKFLOW_FILE = 'wan2.2_img_to_vid.json'

# Session Configuration
SESSION_DIR = Path('sessions')
SESSION_FILE = SESSION_DIR / 'bot.session'

# Ensure required directories exist
os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(COMFYUI_INPUT_DIR, exist_ok=True)
os.makedirs(COMFYUI_OUTPUT_DIR, exist_ok=True) 