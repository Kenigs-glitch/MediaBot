import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Bot Configuration
try:
    API_ID = int(os.getenv('API_ID'))
    API_HASH = os.getenv('API_HASH')
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not all([API_ID, API_HASH, BOT_TOKEN]):
        raise ValueError("Missing required bot configuration")
        
except (ValueError, TypeError) as e:
    raise ValueError(f"Invalid bot configuration: {e}. Please check your .env file.")

ID_WHITELIST = set(int(id_) for id_ in os.getenv('ID_WHITELIST', '').split(',') if id_)

# ComfyUI Configuration
COMFYUI_URL = os.getenv('COMFYUI_URL', 'http://192.168.100.11:8188')
COMFYUI_INPUT_DIR = os.getenv('COMFYUI_INPUT_DIR', '/storage/comfyui/input')
COMFYUI_OUTPUT_DIR = os.getenv('COMFYUI_OUTPUT_DIR', '/storage/comfyui/output')
GENERATION_TIMEOUT = int(os.getenv('GENERATION_TIMEOUT', 3600))

# Workflow Configuration
WORKFLOW_FILE = 'wan2.2_img_to_vid.json'

# Session Configuration
SESSION_DIR = 'sessions'
SESSION_FILE = f'{SESSION_DIR}/bot.session'

# Video Generation Configuration
MAX_FRAMES_PER_SEGMENT = 125  # Maximum frames per video segment
DEFAULT_FPS = 20.0  # Default FPS for concatenated videos
DEFAULT_SEGMENT_FRAMES = 100  # Default number of frames per segment
MAX_TOTAL_FRAMES = 10000  # Maximum total frames for long video generation

# Image Configuration
SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')
DEFAULT_HORIZONTAL_SIZE = (1280, 720)  # width, height for horizontal images
DEFAULT_VERTICAL_SIZE = (720, 1280)  # width, height for vertical images

# Temporary Files Configuration
TEMP_DIR = Path('temp')
TEMP_FRAME_PREFIX = 'last_frame_'
TEMP_VIDEO_PREFIX = 'segment_'

# Ensure required directories exist
os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(COMFYUI_INPUT_DIR, exist_ok=True)
os.makedirs(COMFYUI_OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True) 