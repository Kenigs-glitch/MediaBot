# MediaBot

A Telegram bot that converts images to videos using ComfyUI's image-to-video workflow.

## Features

- Image to video conversion with custom prompts
- Support for both photo and document image uploads
- Automatic image orientation detection and resolution adjustment
- Whitelist-based access control
- Docker containerization
- Clean separation of configuration through environment variables

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- ComfyUI server with image-to-video workflow
- Telegram Bot Token, API ID, and API Hash

## Setup

1. Clone the repository:
```bash
git clone https://github.com/Kenigs-glitch/MediaBot.git
cd MediaBot
```

2. Create a `.env` file with your configuration:
```bash
# Telegram Bot Configuration
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token

# Access Control
ID_WHITELIST=123456789,987654321

# ComfyUI Configuration
COMFYUI_URL=http://192.168.100.11:8188
COMFYUI_INPUT_DIR=/storage/comfyui/input
COMFYUI_OUTPUT_DIR=/storage/comfyui/output

# Timeout Configuration
GENERATION_TIMEOUT=3600  # 1 hour in seconds
```

3. Build and start the bot using Docker Compose:
```bash
docker-compose up -d
```

## Usage

1. Start a chat with your bot on Telegram
2. Send the `/start` command
3. Click the "Image to Video 🎬" button
4. Follow the bot's prompts:
   - Enter a text prompt describing the desired video
   - Send an image (photo or document)
   - Specify the number of frames (2-125)
5. Wait for the bot to process your request and send back the video

## Project Structure

- `bot.py` - Main bot code with Telegram handlers and conversation flow
- `media_utils.py` - Media processing utilities and ComfyUI integration
- `wan2.2_img_to_vid.json` - ComfyUI workflow configuration
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Service orchestration
- `requirements.txt` - Python dependencies

## License

MIT License 