# MediaBot

A Telegram bot that generates videos from images and creates images from text using ComfyUI workflows, with an integrated AI agent for learning content strategies.

## Features

### Core Media Generation
- **Text-to-Image Generation** 🖼️ - Generate images from text prompts using DreamShaper
- **Image/Video to Video Conversion** 🎬 - Convert images and videos to videos with custom prompts
- **Smart Orientation Detection** - Automatically detects portrait vs landscape based on prompt content
- **Support for both photo and document uploads** (images and videos)
- **Long video generation with multiple segments**
- **Multi-prompt format support for batch processing**
- **Automatic media orientation detection and resolution adjustment**
- **Video frame extraction and processing**

### AI Agent Integration
- **🤖 AI-Powered Content Strategy Learning** - Learn strategies entirely from your instructions
- **📊 Performance Tracking & Analytics** - Track content performance and learn from results
- **🎯 Project-Based Organization** - Separate strategies and data per project
- **📈 Continuous Learning** - AI improves strategies based on performance data
- **🔄 Automated Content Creation** - Generate content plans and create videos using learned strategies

### System Features
- **Whitelist-based access control**
- **Docker containerization**
- **Clean separation of configuration through environment variables**
- **ComfyUI container management with automatic workflow switching**

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- ComfyUI server with image-to-video workflow
- Telegram Bot Token, API ID, and API Hash
- Cerebras API key (for AI agent features)

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

# AI Agent Configuration (Optional)
CEREBRAS_API_URL=https://api.cerebras.ai/v1
CEREBRAS_API_KEY=your_cerebras_api_key_here
```

3. Build and start the bot using Docker Compose:
```bash
docker-compose up -d
```

## Usage

### Basic Media Generation

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

### AI Agent Commands

The AI agent learns content strategies entirely from your instructions and creates structured strategies from free-form text input.

#### **1. Learn a Strategy**
```
/ai learn [project] [strategy_name] [instructions]
```

**Example:**
```
/ai learn my_project hook_strategy "Create 10-second hooks leading to 2-minute deep dives for maximum creator rewards"
```

The AI analyzes your instructions and creates a structured strategy with:
- Content type and duration ranges
- Target audience and viral formula
- Monetization strategy and hashtags
- Prompt templates for content generation

#### **2. Create Content**
```
/ai create [project] [topic] [strategy]
```

**Example:**
```
/ai create my_project "Ancient Egyptian secrets" hook_strategy
```

The AI generates a content plan and creates the video using your learned strategy.

#### **3. Track Performance**
```
/ai performance [project] [strategy] [metrics]
```

**Example:**
```
/ai performance my_project hook_strategy "views:50000,likes:2500,shares:500"
```

The AI learns from performance data to improve future strategies.

#### **Complete AI Command List**

**Learning & Strategy Management:**
```
/ai learn [project] [strategy_name] [instructions] - Learn new strategy
/ai strategies [project] - List all strategies for project
```

**Content Creation:**
```
/ai create [project] [topic] [strategy] - Create content
/ai plan [project] [topic] [strategy] - Generate content plan only
```

**Performance & Analytics:**
```
/ai performance [project] [strategy] [metrics] - Update performance data
/ai history [project] [strategy] - View performance history
/ai export [project] - Export all project data
```

#### **AI Agent Usage Examples**

**Example 1: Educational Content**
```
1. /ai learn education_project tutorial_strategy "Create progressive educational content from 15-second basics to 3-minute masterclasses with affiliate opportunities"
2. /ai create education_project "Cooking techniques" tutorial_strategy
3. /ai performance education_project tutorial_strategy "views:45000,likes:2200,shares:400"
```

**Example 2: Historical Documentaries**
```
1. /ai learn history_project doc_strategy "Create historical documentaries with period-accurate visuals, Ken Burns effects, and investigative journalism style"
2. /ai create history_project "World War II mysteries" doc_strategy
3. /ai performance history_project doc_strategy "views:120000,likes:6000,shares:1500"
```

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

### Permission Issues

If you encounter permission errors like "Permission denied: '/storage/comfyui/input/...'", run the permission fix script:

```bash
sudo ./fix_permissions.sh
```

This script will:
- Set the correct ownership for ComfyUI directories
- Ensure the bot container can write to input/output directories
- Fix permissions for both Docker socket access and file operations

Then rebuild and restart the container:

```bash
docker compose down
docker compose up --build -d
```

### Smart Orientation Detection

The bot automatically detects the optimal image orientation based on your prompt:

**Horizontal Orientation (1280x720)** is chosen when the word "horiz" is included in your prompt
- The "horiz" keyword is automatically removed before processing
- Example: "a beautiful sunset horiz" → generates horizontal image

**Vertical Orientation (720x1280)** is the default for all other prompts
- Used when "horiz" is not present in the prompt
- Example: "a portrait of a person" → generates vertical image

### Video Extension

The bot supports using videos as input:
1. Send a video (as media or document)
2. The bot will extract the last frame
3. The frame will be automatically resized to:
   - 1280x720 for horizontal videos
   - 720x1280 for vertical videos
4. Aspect ratio is preserved with center cropping

## Project Structure

### Core Files
- `bot.py` - Main bot code with Telegram handlers and conversation flow
- `txt2img.py` - Text-to-image generation using DreamShaper workflow
- `media_utils.py` - Media processing utilities and ComfyUI integration
- `long_video.py` - Long video generation utilities
- `video_utils.py` - Video processing utilities
- `server_utils.py` - ComfyUI container management

### AI Agent Files
- `ai_agent.py` - AI agent implementation with strategy learning
- `bot_ai_integration.py` - AI agent integration with Telegram bot

### Configuration Files
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

## AI Agent Features

### What the AI Learns

From your instructions, the AI extracts:

**Content Structure**
- Content type (single, series, ladder, documentary)
- Duration ranges (min, max, optimal)
- Viral formula (hook_to_payoff, progressive_learning, etc.)

**Audience & Engagement**
- Target audience description
- Psychological triggers (curiosity, surprise, satisfaction, etc.)
- Hashtag strategy

**Monetization**
- Primary revenue stream (creator_rewards, tiktok_shop, brand_sponsorships)
- Secondary revenue stream (affiliate_marketing, course_sales)
- Target revenue per 1K views

**Content Generation**
- Prompt templates for AI generation
- Content planning structure
- Performance expectations

### Data Storage

**SQLite Database Structure**
- **strategies** - All learned strategies per project
- **content_plans** - Generated content plans
- **performance_data** - Performance metrics and analysis

**Data Export**
Use `/ai export [project]` to get:
- All strategies for the project
- Performance history
- Learning data and analysis

### Best Practices

**Writing Effective Instructions**
1. **Be specific** - "Create 10-second hooks leading to 2-minute deep dives" vs "Make viral content"
2. **Include monetization goals** - "for maximum creator rewards" or "with affiliate opportunities"
3. **Specify content type** - "progressive educational content" or "investigative documentaries"
4. **Mention target audience** - "for fitness enthusiasts" or "for history buffs"

**Project Organization**
1. **Use descriptive project names** - `fitness_tutorials`, `product_reviews`, `historical_docs`
2. **Keep related content in same project** - All fitness content in `fitness_project`
3. **Track performance consistently** - Update metrics for every piece of content
4. **Export data regularly** - Backup your learning data

## Troubleshooting

### Common Issues
1. **Strategy not found** - Use `/ai strategies [project]` to see available strategies
2. **Content creation fails** - Check ComfyUI server status
3. **Performance update fails** - Verify metrics format (views:50000,likes:2500)
4. **Database errors** - Check file permissions for `ai_agent_data.db`
5. **Docker access issues** - Run `./setup_docker_access.sh`
6. **Permission errors** - Run `sudo ./fix_permissions.sh`

### Getting Help
- Check bot logs for error messages
- Verify Cerebras API key is configured (for AI features)
- Ensure all dependencies are installed
- Test with simple instructions first

## License

MIT License 