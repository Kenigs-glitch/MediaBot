# MediaBot

A Telegram bot that converts images and videos to videos using ComfyUI's image-to-video workflow.

## Features

- Image/video to video conversion with custom prompts
- Support for both photo and document uploads (images and videos)
- Long video generation with multiple segments
- Multi-prompt format support for batch processing
- Automatic media orientation detection and resolution adjustment
- Video frame extraction and processing
- Whitelist-based access control
- Docker containerization
- Clean separation of configuration through environment variables

## Prerequisites

- Python 3.12+
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

### Basic Usage

1. Start a chat with your bot on Telegram
2. Send the `/start` command
3. Choose an option:
   - "Short Video 🎬" for single segment videos
   - "Long Video 🎥" for multi-segment videos
4. Follow the bot's prompts:
   - Enter a text prompt describing the desired video
   - Send an image or video (as photo/video or document)
   - For short videos: specify frames (2-125)
   - For long videos: specify frames for each segment
5. Wait for the bot to process your request and send back the video

### Multi-Prompt Format

You can send an image/video with a caption in the following format for batch processing:
```
Prompt1
Frames_N1
Prompt2
Frames_N2
...
```

Example:
```
A beautiful sunset
100
Night sky with stars
75
Morning sunrise
50
```

This will generate a video with three segments using the specified prompts and frame counts.

### Video Extension

The bot supports using videos as input:
1. Send a video (as media or document)
2. The bot will extract the last frame
3. The frame will be automatically resized to:
   - 1280x720 for horizontal videos
   - 720x1280 for vertical videos
4. Aspect ratio is preserved with center cropping

## Project Structure

- `bot.py` - Main bot code with Telegram handlers and conversation flow
- `media_utils.py` - Media processing utilities and ComfyUI integration
- `long_video.py` - Long video generation utilities
- `wan2.2_img_to_vid.json` - ComfyUI workflow configuration
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Service orchestration
- `requirements.txt` - Python dependencies

## License

MIT License 