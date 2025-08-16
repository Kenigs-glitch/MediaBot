# AI Agent Integration for MediaBot

This AI agent integration transforms your MediaBot into an intelligent TikTok content creation system using Cerebras API. The agent automatically generates viral content based on proven psychological triggers and viral formulas from the TikTok strategy document.

## Features

### 🤖 **Intelligent Content Creation**
- **Automated Content Planning**: AI generates complete content plans with titles, descriptions, and optimized prompts
- **Trend Analysis**: Real-time analysis of trending topics for maximum viral potential
- **Strategy-Based Generation**: Four proven content strategies based on TikTok research
- **Prompt Optimization**: AI-optimized prompts for WAN 2.1/2.2 video generation

### 📊 **Content Strategies**
1. **Invisible Expertise** - DIY and professional tips (21s, $0.80/1K views)
2. **Historical Humor** - Historical facts with humor (34s, $0.60/1K views)
3. **Marine Education** - Ocean and marine life content (28s, $0.90/1K views)
4. **Geographic Micro-Niche** - Cultural and travel content (25s, $0.70/1K views)

### 🎯 **Viral Formulas**
- **Hook-Body-Conclusion**: 3s hook → 15s content → 3s conclusion
- **Transformation Reveal**: Setup → dramatic change → final reveal
- **Mystery Hook**: Intrigue → suspense → resolution

## Setup

### 1. Environment Variables
Add these to your `.env` file:

```bash
# Cerebras API Configuration
CEREBRAS_API_URL=https://api.cerebras.ai/v1
CEREBRAS_API_KEY=your_cerebras_api_key_here

# AI Agent Settings
MAX_DAILY_CONTENT=5
CONTENT_CREATION_TIMEOUT=3600
MIN_EXPECTED_VIEWS=10000
TARGET_ENGAGEMENT_RATE=0.05
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Restart Bot
```bash
docker compose down
docker compose up --build -d
```

## Usage

### Basic Commands

#### Create Content
```
/ai create [strategy] [topic]
```
**Examples:**
- `/ai create invisible_expertise "life hacks"`
- `/ai create marine_education "ocean mysteries"`
- `/ai create historical_humor "ancient Rome"`

#### Generate Content Plans
```
/ai plan [strategy]
```
**Examples:**
- `/ai plan marine_education`
- `/ai plan invisible_expertise`

#### Analyze Trends
```
/ai analyze
```
Shows current trending topics for content inspiration.

#### Check Status
```
/ai status
```
Shows current AI agent activity and progress.

#### Stop Tasks
```
/ai stop
```
Cancels running AI agent tasks.

### Advanced Usage

#### Content Creation Process
1. **Strategy Selection**: Choose from 4 proven content strategies
2. **Topic Input**: Provide a topic or let AI analyze trends
3. **AI Planning**: Agent generates complete content plan
4. **Prompt Optimization**: AI optimizes prompts for video generation
5. **Content Creation**: Uses existing MediaBot functions to create content
6. **Results**: Returns detailed content information and performance metrics

#### Strategy Details

**Invisible Expertise Strategy:**
- Target: DIY enthusiasts, professionals
- Duration: 21 seconds
- Monetization: $0.80 per 1K views
- Hashtags: #DIY, #HowTo, #LifeHacks, #ExpertTips
- Viral Formula: Hook-Body-Conclusion

**Historical Humor Strategy:**
- Target: History buffs, comedy lovers
- Duration: 34 seconds
- Monetization: $0.60 per 1K views
- Hashtags: #History, #Funny, #HistoricalFacts, #Comedy
- Viral Formula: Transformation Reveal

**Marine Education Strategy:**
- Target: Nature lovers, science enthusiasts
- Duration: 28 seconds
- Monetization: $0.90 per 1K views
- Hashtags: #Ocean, #MarineLife, #Science, #Nature
- Viral Formula: Mystery Hook

**Geographic Micro-Niche Strategy:**
- Target: Cultural enthusiasts, travelers
- Duration: 25 seconds
- Monetization: $0.70 per 1K views
- Hashtags: #Culture, #Travel, #Heritage, #Community
- Viral Formula: Hook-Body-Conclusion

## Technical Architecture

### AI Agent Components

1. **TikTokAIAgent** (`ai_agent.py`)
   - Core AI agent with Cerebras API integration
   - Content strategy management
   - Performance analysis and optimization

2. **Configuration** (`ai_agent_config.py`)
   - Content strategies and viral formulas
   - Performance metrics and quality filters
   - Prompt optimization settings

3. **Bot Integration** (`bot_ai_integration.py`)
   - Telegram bot command handlers
   - Progress tracking and status updates
   - Task management and error handling

### Integration with MediaBot

The AI agent seamlessly integrates with existing MediaBot functions:

- **Text-to-Image**: Uses `generate_image_from_text()` for initial content
- **Video Generation**: Uses `process_image_to_video()` and `LongVideoGenerator`
- **ComfyUI Management**: Leverages existing server management functions
- **File Management**: Uses existing input/output directory structure

### Content Creation Pipeline

```
1. User Command → /ai create [strategy] [topic]
2. AI Agent Initialization
3. Trend Analysis (Cerebras API)
4. Content Plan Generation
5. Prompt Optimization
6. MediaBot Integration
   ├── Image Generation (DreamShaper)
   ├── Video Creation (WAN 2.1/2.2)
   └── ComfyUI Management
7. Results and Performance Metrics
```

## Performance Optimization

### Content Quality Filters
- **Resolution**: 1080x1920 (TikTok vertical format)
- **Duration**: 10-60 seconds optimal
- **File Size**: Max 50MB
- **Aspect Ratio**: 9:16 required

### Prompt Optimization
The AI agent automatically optimizes prompts for:
- Professional camera shots
- Natural movement and realistic physics
- Mobile-optimized viewing
- Avoidance of uncanny valley effects
- Cinematic quality and documentary realism

### Performance Metrics
- **Views**: Target 50,000+ (30% weight)
- **Likes**: Target 2,500+ (20% weight)
- **Shares**: Target 500+ (25% weight)
- **Comments**: Target 200+ (15% weight)
- **Saves**: Target 100+ (10% weight)

## Error Handling

### Common Issues

1. **Cerebras API Errors**
   - Check API key configuration
   - Verify API endpoint accessibility
   - Monitor rate limits

2. **Content Creation Failures**
   - Check ComfyUI server status
   - Verify input/output directories
   - Monitor disk space

3. **Task Cancellation**
   - Use `/ai stop` to cancel running tasks
   - Check task status with `/ai status`

### Debugging

Enable detailed logging by setting log level to DEBUG:
```python
logger.add(sys.stdout, level="DEBUG")
```

## Monitoring and Analytics

### Performance Tracking
- Content creation success rates
- Strategy performance comparison
- Trend analysis accuracy
- User engagement metrics

### Content Analytics
- Expected vs actual performance
- Strategy effectiveness
- Monetization potential
- Viral coefficient analysis

## Future Enhancements

### Planned Features
1. **Multi-Platform Support**: Instagram Reels, YouTube Shorts
2. **Advanced Analytics**: Real-time performance tracking
3. **A/B Testing**: Automated content optimization
4. **Brand Integration**: Sponsored content management
5. **Community Features**: User-generated content collaboration

### API Integrations
- TikTok Content Posting API
- Social media analytics platforms
- Content management systems
- E-commerce platforms for monetization

## Security and Compliance

### Content Safety
- Automated content moderation
- Brand safety verification
- Copyright compliance checking
- Platform policy adherence

### Data Privacy
- User data encryption
- Secure API communication
- GDPR compliance
- Data retention policies

## Support

### Troubleshooting
1. Check environment variables
2. Verify Cerebras API access
3. Monitor ComfyUI server status
4. Review error logs

### Getting Help
- Check the main README.md for MediaBot setup
- Review error messages in bot logs
- Verify all dependencies are installed
- Test Cerebras API connectivity

---

**Note**: This AI agent integration requires a valid Cerebras API key and follows the TikTok content strategy guidelines for optimal performance and compliance. 