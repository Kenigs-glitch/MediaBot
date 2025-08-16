# AI Agent for MediaBot

A clean, simple AI agent that learns content strategies entirely from your instructions. No pre-defined niches or scenarios - the AI builds strategies from scratch based on your specific requirements.

## 🎯 **Core Concept**

**The AI learns from your instructions and creates structured strategies from free-form text input.**

- **No pre-defined strategies** - Everything is built from your instructions
- **Project-based separation** - Each project has its own isolated context
- **Simple database storage** - SQLite database for strategies and performance data
- **Clear, straightforward commands** - Easy to understand and use

## 🚀 **How It Works**

### **1. Learn a Strategy**
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

### **2. Create Content**
```
/ai create [project] [topic] [strategy]
```

**Example:**
```
/ai create my_project "Ancient Egyptian secrets" hook_strategy
```

The AI generates a content plan and creates the video using your learned strategy.

### **3. Track Performance**
```
/ai performance [project] [strategy] [metrics]
```

**Example:**
```
/ai performance my_project hook_strategy "views:50000,likes:2500,shares:500"
```

The AI learns from performance data to improve future strategies.

## 📋 **Complete Command List**

### **Learning & Strategy Management**
```
/ai learn [project] [strategy_name] [instructions] - Learn new strategy
/ai strategies [project] - List all strategies for project
```

### **Content Creation**
```
/ai create [project] [topic] [strategy] - Create content
/ai plan [project] [topic] [strategy] - Generate content plan only
```

### **Performance & Analytics**
```
/ai performance [project] [strategy] [metrics] - Update performance data
/ai history [project] [strategy] - View performance history
/ai export [project] - Export all project data
```

## 🎯 **Usage Examples**

### **Example 1: Educational Content**
```
1. /ai learn education_project tutorial_strategy "Create progressive educational content from 15-second basics to 3-minute masterclasses with affiliate opportunities"
2. /ai create education_project "Cooking techniques" tutorial_strategy
3. /ai performance education_project tutorial_strategy "views:45000,likes:2200,shares:400"
```

### **Example 2: Historical Documentaries**
```
1. /ai learn history_project doc_strategy "Create historical documentaries with period-accurate visuals, Ken Burns effects, and investigative journalism style"
2. /ai create history_project "World War II mysteries" doc_strategy
3. /ai performance history_project doc_strategy "views:120000,likes:6000,shares:1500"
```

### **Example 3: Product Reviews**
```
1. /ai learn review_project review_strategy "Create product review videos with 10-second hooks, detailed analysis, and affiliate links for maximum monetization"
2. /ai create review_project "iPhone 15 review" review_strategy
3. /ai performance review_project review_strategy "views:75000,likes:3500,shares:800"
```

## 🗄️ **Project-Based Organization**

Each project is completely isolated:

- **Separate strategies** - No mixing between projects
- **Independent performance data** - Each project tracks its own metrics
- **Isolated learning** - Strategies improve within their project context
- **Clean data export** - Export data per project

**Project Examples:**
- `education_project` - Educational content strategies
- `history_project` - Historical documentary strategies
- `review_project` - Product review strategies
- `comedy_project` - Comedy content strategies
- `fitness_project` - Fitness tutorial strategies

## 📊 **What the AI Learns**

From your instructions, the AI extracts:

### **Content Structure**
- Content type (single, series, ladder, documentary)
- Duration ranges (min, max, optimal)
- Viral formula (hook_to_payoff, progressive_learning, etc.)

### **Audience & Engagement**
- Target audience description
- Psychological triggers (curiosity, surprise, satisfaction, etc.)
- Hashtag strategy

### **Monetization**
- Primary revenue stream (creator_rewards, tiktok_shop, brand_sponsorships)
- Secondary revenue stream (affiliate_marketing, course_sales)
- Target revenue per 1K views

### **Content Generation**
- Prompt templates for AI generation
- Content planning structure
- Performance expectations

## 💾 **Data Storage**

### **SQLite Database Structure**
- **strategies** - All learned strategies per project
- **content_plans** - Generated content plans
- **performance_data** - Performance metrics and analysis

### **Data Export**
Use `/ai export [project]` to get:
- All strategies for the project
- Performance history
- Learning data and analysis

## 🔧 **Setup**

### **Environment Variables**
```bash
# Cerebras API Configuration
CEREBRAS_API_URL=https://api.cerebras.ai/v1
CEREBRAS_API_KEY=your_cerebras_api_key_here
```

### **Installation**
```bash
pip install -r requirements.txt
docker compose up --build -d
```

## 🎯 **Best Practices**

### **Writing Effective Instructions**
1. **Be specific** - "Create 10-second hooks leading to 2-minute deep dives" vs "Make viral content"
2. **Include monetization goals** - "for maximum creator rewards" or "with affiliate opportunities"
3. **Specify content type** - "progressive educational content" or "investigative documentaries"
4. **Mention target audience** - "for fitness enthusiasts" or "for history buffs"

### **Project Organization**
1. **Use descriptive project names** - `fitness_tutorials`, `product_reviews`, `historical_docs`
2. **Keep related content in same project** - All fitness content in `fitness_project`
3. **Track performance consistently** - Update metrics for every piece of content
4. **Export data regularly** - Backup your learning data

### **Strategy Naming**
1. **Use descriptive names** - `hook_strategy`, `tutorial_strategy`, `review_strategy`
2. **Be consistent** - Use similar naming patterns within a project
3. **Keep it simple** - Avoid complex names that are hard to type

## 🔄 **Workflow Example**

### **Complete Workflow**
```
1. Start a new project
   /ai learn my_new_project content_strategy "Your detailed instructions here"

2. Create content
   /ai create my_new_project "Your topic" content_strategy

3. Track performance
   /ai performance my_new_project content_strategy "views:50000,likes:2500,shares:500"

4. View history
   /ai history my_new_project

5. Export data
   /ai export my_new_project
```

## 🚀 **Advanced Usage**

### **Multiple Strategies per Project**
```
/ai learn fitness_project beginner_strategy "15-second quick tips for fitness beginners"
/ai learn fitness_project advanced_strategy "3-minute detailed workout tutorials for advanced users"
/ai learn fitness_project transformation_strategy "Before/after transformation content with progress tracking"
```

### **Performance-Based Learning**
```
1. Create content with strategy
2. Post to TikTok
3. Update performance: /ai performance project strategy "views:X,likes:Y,shares:Z"
4. AI learns and improves strategy
5. Create more content with improved strategy
```

## 🛠️ **Troubleshooting**

### **Common Issues**
1. **Strategy not found** - Use `/ai strategies [project]` to see available strategies
2. **Content creation fails** - Check ComfyUI server status
3. **Performance update fails** - Verify metrics format (views:50000,likes:2500)
4. **Database errors** - Check file permissions for `ai_agent_data.db`

### **Getting Help**
- Check bot logs for error messages
- Verify Cerebras API key is configured
- Ensure all dependencies are installed
- Test with simple instructions first

## 📈 **Benefits**

### **Simplicity**
- No complex pre-defined strategies
- Clear, straightforward commands
- Easy to understand and use

### **Flexibility**
- Build strategies from any instructions
- Adapt to any content niche
- Learn from real performance data

### **Organization**
- Project-based separation
- Clean data management
- Easy data export and backup

### **Learning**
- Continuous improvement from performance data
- Strategy evolution based on real results
- Personalized content optimization

---

**The AI Agent transforms your MediaBot into a learning system that builds strategies entirely from your instructions, with clean project separation and straightforward commands.** 