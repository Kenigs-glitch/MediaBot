import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

from ai_agent import TikTokAIAgent, create_tiktok_content_agent
from ai_agent_config import ai_config, CONTENT_STRATEGIES
from bot import bot, is_authorized, show_initial_menu

# AI Agent integration state
AI_AGENT_STATE = {}
AI_AGENT_TASKS = {}

async def handle_ai_agent_command(event, command_parts: List[str]):
    """Handle AI agent commands from Telegram bot"""
    user = await event.get_sender()
    user_id = user.id
    
    if not is_authorized(user_id):
        await event.respond("You are not authorized to use AI agent commands.")
        return
    
    if len(command_parts) < 2:
        await show_ai_agent_help(event)
        return
    
    subcommand = command_parts[1].lower()
    
    try:
        if subcommand == "create":
            await handle_create_content(event, command_parts[2:])
        elif subcommand == "plan":
            await handle_generate_plan(event, command_parts[2:])
        elif subcommand == "analyze":
            await handle_analyze_trends(event)
        elif subcommand == "status":
            await handle_agent_status(event)
        elif subcommand == "stop":
            await handle_stop_agent(event, user_id)
        else:
            await show_ai_agent_help(event)
            
    except Exception as e:
        logger.error(f"Error in AI agent command: {e}")
        await event.respond(f"An error occurred: {str(e)}")

async def show_ai_agent_help(event):
    """Show AI agent help menu"""
    help_text = """
🤖 **AI Agent Commands**

/ai create [strategy] [topic] - Create content using AI agent
/ai plan [strategy] - Generate content plan for strategy
/ai analyze - Analyze current trending topics
/ai status - Check AI agent status
/ai stop - Stop running AI agent tasks

**Available Strategies:**
• invisible_expertise - DIY and professional tips
• historical_humor - Historical facts with humor
• marine_education - Ocean and marine life content
• geographic_micro_niche - Cultural and travel content

**Examples:**
/ai create invisible_expertise "life hacks"
/ai plan marine_education
/ai analyze
"""
    await event.respond(help_text)

async def handle_create_content(event, args: List[str]):
    """Handle content creation command"""
    user = await event.get_sender()
    user_id = user.id
    
    if len(args) < 2:
        await event.respond("Usage: /ai create [strategy] [topic]\nExample: /ai create invisible_expertise 'life hacks'")
        return
    
    strategy_name = args[0].lower()
    topic = " ".join(args[1:])
    
    if strategy_name not in CONTENT_STRATEGIES:
        await event.respond(f"Unknown strategy: {strategy_name}\nAvailable: {', '.join(CONTENT_STRATEGIES.keys())}")
        return
    
    # Check if user already has a running task
    if user_id in AI_AGENT_TASKS and not AI_AGENT_TASKS[user_id].done():
        await event.respond("You already have a content creation task running. Use /ai stop to cancel it first.")
        return
    
    await event.respond(f"🤖 Starting AI content creation...\nStrategy: {strategy_name}\nTopic: {topic}")
    
    # Create and run AI agent task
    task = asyncio.create_task(
        run_ai_content_creation(event, user_id, strategy_name, topic)
    )
    AI_AGENT_TASKS[user_id] = task
    
    # Store state
    AI_AGENT_STATE[user_id] = {
        'status': 'creating',
        'strategy': strategy_name,
        'topic': topic,
        'start_time': datetime.now(),
        'progress': 0
    }

async def run_ai_content_creation(event, user_id: int, strategy_name: str, topic: str):
    """Run AI content creation process"""
    try:
        # Update status
        await update_ai_status(event, user_id, "Initializing AI agent...", 10)
        
        # Create AI agent
        agent = await create_tiktok_content_agent()
        
        await update_ai_status(event, user_id, "Analyzing trending topics...", 20)
        
        # Analyze trends
        trending_topics = await agent.analyze_trending_topics()
        
        await update_ai_status(event, user_id, "Generating content plan...", 40)
        
        # Get strategy
        strategy_data = CONTENT_STRATEGIES[strategy_name]
        
        # Generate content plan
        plan = await agent.generate_content_plan(
            agent.content_strategies[strategy_name], 
            topic
        )
        
        if not plan:
            await event.respond("❌ Failed to generate content plan. Please try again.")
            return
        
        await update_ai_status(event, user_id, "Optimizing prompts...", 60)
        
        # Optimize prompt
        optimized_prompt = await agent.generate_optimized_prompt(
            plan.prompt, 
            agent.content_strategies[strategy_name]
        )
        plan.prompt = optimized_prompt
        
        await update_ai_status(event, user_id, "Creating content with MediaBot...", 80)
        
        # Create content using existing MediaBot functions
        content_result = await agent.create_content(plan)
        
        if content_result:
            await update_ai_status(event, user_id, "✅ Content creation completed!", 100)
            
            # Send results
            result_message = f"""
🎉 **AI Content Creation Complete!**

📝 **Title:** {plan.title}
📋 **Description:** {plan.description}
⏱️ **Duration:** {plan.target_duration} seconds
🏷️ **Hashtags:** {' '.join(plan.hashtags[:3])}
📊 **Expected Views:** {plan.expected_performance.get('views', 'N/A'):,}

🎯 **Strategy:** {strategy_name}
📈 **Monetization Potential:** ${strategy_data['monetization_potential']:.2f} per 1K views

The content has been created and is ready for review!
"""
            await event.respond(result_message)
            
            # Update state
            AI_AGENT_STATE[user_id] = {
                'status': 'completed',
                'strategy': strategy_name,
                'topic': topic,
                'completion_time': datetime.now(),
                'plan': plan.__dict__,
                'result': content_result
            }
        else:
            await event.respond("❌ Content creation failed. Please check the logs and try again.")
            AI_AGENT_STATE[user_id]['status'] = 'failed'
            
    except Exception as e:
        logger.error(f"Error in AI content creation: {e}")
        await event.respond(f"❌ An error occurred during content creation: {str(e)}")
        AI_AGENT_STATE[user_id]['status'] = 'error'
        AI_AGENT_STATE[user_id]['error'] = str(e)
    
    finally:
        # Clean up task
        if user_id in AI_AGENT_TASKS:
            del AI_AGENT_TASKS[user_id]

async def handle_generate_plan(event, args: List[str]):
    """Handle content plan generation"""
    user = await event.get_sender()
    user_id = user.id
    
    if len(args) < 1:
        await event.respond("Usage: /ai plan [strategy]\nExample: /ai plan marine_education")
        return
    
    strategy_name = args[0].lower()
    
    if strategy_name not in CONTENT_STRATEGIES:
        await event.respond(f"Unknown strategy: {strategy_name}\nAvailable: {', '.join(CONTENT_STRATEGIES.keys())}")
        return
    
    await event.respond(f"🤖 Generating content plan for {strategy_name}...")
    
    try:
        agent = await create_tiktok_content_agent()
        
        # Generate sample plans
        plans = []
        for i in range(3):  # Generate 3 sample plans
            plan = await agent.generate_content_plan(
                agent.content_strategies[strategy_name],
                f"Sample topic {i+1}"
            )
            if plan:
                plans.append(plan)
        
        if plans:
            plan_message = f"""
📋 **Content Plans for {strategy_name}**

"""
            for i, plan in enumerate(plans, 1):
                plan_message += f"""
**Plan {i}:**
📝 {plan.title}
⏱️ {plan.target_duration}s
🏷️ {' '.join(plan.hashtags[:3])}
📊 Expected: {plan.expected_performance.get('views', 'N/A'):,} views

"""
            
            await event.respond(plan_message)
        else:
            await event.respond("❌ Failed to generate content plans.")
            
    except Exception as e:
        logger.error(f"Error generating plans: {e}")
        await event.respond(f"❌ Error generating plans: {str(e)}")

async def handle_analyze_trends(event):
    """Handle trend analysis"""
    await event.respond("🤖 Analyzing current trending topics...")
    
    try:
        agent = await create_tiktok_content_agent()
        trending_topics = await agent.analyze_trending_topics()
        
        if trending_topics:
            trends_message = "📈 **Current Trending Topics:**\n\n"
            for i, topic in enumerate(trending_topics[:10], 1):
                trends_message += f"{i}. {topic}\n"
            
            trends_message += "\n💡 Use these topics with /ai create [strategy] [topic]"
            await event.respond(trends_message)
        else:
            await event.respond("❌ Failed to analyze trending topics.")
            
    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        await event.respond(f"❌ Error analyzing trends: {str(e)}")

async def handle_agent_status(event):
    """Handle agent status check"""
    user = await event.get_sender()
    user_id = user.id
    
    if user_id not in AI_AGENT_STATE:
        await event.respond("🤖 No AI agent activity found for your account.")
        return
    
    state = AI_AGENT_STATE[user_id]
    
    status_message = f"""
🤖 **AI Agent Status**

📊 **Status:** {state['status'].title()}
🎯 **Strategy:** {state.get('strategy', 'N/A')}
📝 **Topic:** {state.get('topic', 'N/A')}
⏰ **Started:** {state.get('start_time', 'N/A')}

"""
    
    if state['status'] == 'creating':
        progress = state.get('progress', 0)
        status_message += f"📈 **Progress:** {progress}%"
        
        # Check if task is running
        if user_id in AI_AGENT_TASKS and not AI_AGENT_TASKS[user_id].done():
            status_message += "\n🔄 **Task:** Running"
        else:
            status_message += "\n⏸️ **Task:** Paused"
    
    elif state['status'] == 'completed':
        completion_time = state.get('completion_time', 'N/A')
        status_message += f"✅ **Completed:** {completion_time}"
    
    elif state['status'] == 'failed':
        error = state.get('error', 'Unknown error')
        status_message += f"❌ **Error:** {error}"
    
    await event.respond(status_message)

async def handle_stop_agent(event, user_id: int):
    """Handle stopping AI agent tasks"""
    if user_id in AI_AGENT_TASKS:
        task = AI_AGENT_TASKS[user_id]
        if not task.done():
            task.cancel()
            await event.respond("🛑 AI agent task cancelled.")
        else:
            await event.respond("ℹ️ No running AI agent tasks found.")
    else:
        await event.respond("ℹ️ No AI agent tasks found for your account.")

async def update_ai_status(event, user_id: int, message: str, progress: int):
    """Update AI agent status and progress"""
    if user_id in AI_AGENT_STATE:
        AI_AGENT_STATE[user_id]['progress'] = progress
    
    # Send progress update
    progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
    status_message = f"🤖 {message}\n📊 [{progress_bar}] {progress}%"
    
    await event.respond(status_message)

# Integration with existing bot
def register_ai_agent_handlers():
    """Register AI agent handlers with the existing bot"""
    
    @bot.on(events.NewMessage(pattern='/ai'))
    async def ai_agent_handler(event):
        """Handle AI agent commands"""
        command_parts = event.text.strip().split()
        await handle_ai_agent_command(event, command_parts)

# Export functions for use in main bot
__all__ = [
    'handle_ai_agent_command',
    'register_ai_agent_handlers',
    'AI_AGENT_STATE',
    'AI_AGENT_TASKS'
] 