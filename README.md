# MediaBot

A Telegram bot that generates videos from images and creates images from text using ComfyUI workflows.

## Features

- **Text-to-Image Generation** 🖼️ - Generate images from text prompts using DreamShaper
- **Image/Video to Video Conversion** 🎬 - Convert images and videos to videos with custom prompts
- **Smart Orientation Detection** - Automatically detects portrait vs landscape based on prompt content
- **Support for both photo and document uploads** (images and videos)
- **Long video generation with multiple segments**
- **Multi-prompt format support for batch processing**
- **Automatic media orientation detection and resolution adjustment**
- **Video frame extraction and processing**
- **Whitelist-based access control**
- **Docker containerization**
- **Clean separation of configuration through environment variables**

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
   - **"Generate Image 🖼️"** - Create images from text prompts
   - **"Short Video 🎬"** - Generate single segment videos from images
   - **"Long Video 🎥"** - Generate multi-segment videos from images

#### Text-to-Image Generation
1. Select "Generate Image 🖼️"
2. Enter a detailed prompt describing the image you want to create
3. The bot will automatically:
   - Detect the optimal orientation (portrait/landscape) based on your prompt
   - Generate a 720x1280 (portrait) or 1280x720 (landscape) image
   - Send the generated image back to you

#### Video Generation
1. Select "Short Video 🎬" or "Long Video 🎥"
2. Enter a text prompt describing the desired video
3. Send an image or video (as photo/video or document)
4. For short videos: specify frames (2-125)
5. For long videos: specify frames for each segment
6. Wait for the bot to process your request and send back the video

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

### Server Management

The bot includes admin commands to manage the ComfyUI server:

- `/admin status` - Check ComfyUI container status
- `/admin restart` - Restart ComfyUI container
- `/admin force_restart` - Force restart ComfyUI (stop, remove, and start fresh)
- `/admin start` - Start ComfyUI if it's not running

These commands are only available to users in the `ID_WHITELIST`.

**Security Note**: The bot container has access to the Docker socket to manage ComfyUI. This provides full Docker daemon access, so ensure only trusted users are in the whitelist.

### Docker Access Setup

If you encounter "User has no access to docker socket" errors, run the setup script:

```bash
./setup_docker_access.sh
```

This script will:
- Check if the docker group exists and get its GID
- Verify your user is in the docker group
- Check docker socket permissions
- Export the correct environment variables

Then rebuild and restart the container:

```bash
docker-compose build
docker-compose up -d
```

### Smart Orientation Detection

The bot automatically detects the optimal image orientation based on your prompt content:

**Portrait Orientation (720x1280)** is chosen for prompts containing:
- Portrait, vertical, tall, standing
- Person, human, figure, character
- Full body, close up, face, head, bust
- Selfie, profile, portrait shot

**Landscape Orientation (1280x720)** is chosen for prompts containing:
- Landscape, horizontal, wide, panorama
- Scenery, nature, cityscape, street
- Beach, mountain, forest, environment
- Group, crowd, scene, background, setting

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
- `txt2img.py` - Text-to-image generation using DreamShaper workflow
- `media_utils.py` - Media processing utilities and ComfyUI integration
- `long_video.py` - Long video generation utilities
- `dreamshaper_txt_to_img.json` - DreamShaper text-to-image workflow configuration
- `wan2.2_img_to_vid.json` - ComfyUI image-to-video workflow configuration
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Service orchestration
- `requirements.txt` - Python dependencies

## Workflows

The bot uses two different ComfyUI workflows:

### DreamShaper Text-to-Image (`dreamshaper_txt_to_img.json`)
- **Purpose**: Generate images from text prompts
- **Model**: DreamShaperXL_Lightning.safetensors
- **Features**: 
  - Automatic prompt replacement
  - Dynamic resolution based on content
  - High-quality image generation
  - Optimized for both portrait and landscape orientations

### Image-to-Video (`wan2.2_img_to_vid.json`)
- **Purpose**: Convert images to videos
- **Features**:
  - Custom prompt integration
  - Variable frame count
  - Video extension support
  - Multi-segment processing

## License

MIT License 