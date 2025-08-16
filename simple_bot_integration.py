import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

from simple_ai_agent import SimpleAIAgent, create_simple_ai_agent
from bot import bot, is_authorized, show_initial_menu

# Simple AI Agent instances (one per project)
SIMPLE_AGENT_INSTANCES = {}
SIMPLE_AGENT_TASKS = {}

async def handle_simple_ai_command(event, command_parts: List[str]):
    """Handle simple AI agent commands from Telegram bot"""
    user = await event.get_sender()
    user_id = user.id
    
    if not is_authorized(user_id):
        await event.respond("You are not authorized to use AI agent commands.")
        return
    
    if len(command_parts) < 2:
        await show_simple_ai_help(event)
        return
    
    subcommand = command_parts[1].lower()
    
    try:
        if subcommand == "learn":
            await handle_learn_strategy(event, command_parts[2:])
        elif subcommand == "create":
            await handle_create_content(event, command_parts[2:])
        elif subcommand == "strategies":
            await handle_list_strategies(event)
        elif subcommand == "plan":
            await handle_generate_plan(event, command_parts[2:])
        elif subcommand == "performance":
            await handle_update_performance(event, command_parts[2:])
        elif subcommand == "history":
            await handle_view_history(event, command_parts[2:])
        elif subcommand == "export":
            await handle_export_data(event, command_parts[2:])
        else:
            await show_simple_ai_help(event)
            
    except Exception as e:
        logger.error(f"Error in simple AI agent command: {e}")
        await event.respond(f"An error occurred: {str(e)}")

async def show_simple_ai_help(event):
    """Show simple AI agent help menu"""
    help_text = """
🤖 **Simple AI Agent Commands**

**Learning & Strategy:**
/ai learn [project] [strategy_name] [instructions] - Learn new strategy
/ai strategies [project] - List strategies for project

**Content Creation:**
/ai create [project] [topic] [strategy] - Create content
/ai plan [project] [topic] [strategy] - Generate content plan

**Performance & Data:**
/ai performance [project] [strategy] [metrics] - Update performance
/ai history [project] [strategy] - View performance history
/ai export [project] - Export project data

**Examples:**

**Learn a new strategy:**
/ai learn my_project hook_strategy "Create 10-second hooks leading to 2-minute deep dives for maximum creator rewards"

**Create content:**
/ai create my_project "Ancient Egyptian secrets" hook_strategy

**Update performance:**
/ai performance my_project hook_strategy "views:50000,likes:2500,shares:500"

**View strategies:**
/ai strategies my_project

**Generate plan:**
/ai plan my_project "Cooking masterclass" hook_strategy
"""
    await event.respond(help_text)

async def handle_learn_strategy(event, args: List[str]):
    """Handle strategy learning"""
    user = await event.get_sender()
    user_id = user.id
    
    if len(args) < 3:
        await event.respond("Usage: /ai learn [project] [strategy_name] [instructions]\nExample: /ai learn my_project hook_strategy 'Create 10-second hooks leading to 2-minute deep dives'")
        return
    
    project_id = args[0]
    strategy_name = args[1]
    instructions = " ".join(args[2:])
    
    await event.respond(f"🤖 Learning new strategy...\n\n📁 Project: {project_id}\n🎯 Strategy: {strategy_name}\n📝 Instructions: {instructions}")
    
    try:
        # Get or create agent for project
        if project_id not in SIMPLE_AGENT_INSTANCES:
            SIMPLE_AGENT_INSTANCES[project_id] = await create_simple_ai_agent(project_id)
        
        agent = SIMPLE_AGENT_INSTANCES[project_id]
        
        # Learn strategy
        result = await agent.learn_strategy(instructions, strategy_name)
        
        if result['status'] == 'success':
            strategy = result['strategy']
            
            result_message = f"""
✅ **Strategy Learned Successfully!**

📁 **Project:** {project_id}
🎯 **Strategy:** {strategy_name}
📋 **Description:** {strategy['description']}

📊 **Content Type:** {strategy['content_type']}
⏱️ **Duration:** {strategy['duration_range']['min']}-{strategy['duration_range']['max']}s (optimal: {strategy['duration_range']['optimal']}s)
🎭 **Viral Formula:** {strategy['viral_formula']}
👥 **Target Audience:** {strategy['target_audience']}

💰 **Monetization:**
• Primary: {strategy['monetization_strategy']['primary']}
• Secondary: {strategy['monetization_strategy']['secondary']}
• Target Revenue: ${strategy['monetization_strategy']['target_revenue_per_1k_views']}/1K views

🏷️ **Hashtags:** {', '.join(strategy['hashtags'][:5])}

💡 **Next Step:** Use `/ai create {project_id} [topic] {strategy_name}` to create content!
"""
            await event.respond(result_message)
        else:
            await event.respond(f"❌ Failed to learn strategy: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error learning strategy: {e}")
        await event.respond(f"❌ Error learning strategy: {str(e)}")

async def handle_create_content(event, args: List[str]):
    """Handle content creation"""
    user = await event.get_sender()
    user_id = user.id
    
    if len(args) < 3:
        await event.respond("Usage: /ai create [project] [topic] [strategy]\nExample: /ai create my_project 'Ancient Egyptian secrets' hook_strategy")
        return
    
    project_id = args[0]
    topic = args[1]
    strategy_name = args[2]
    
    # Check if user already has a running task
    task_key = f"{user_id}_{project_id}"
    if task_key in SIMPLE_AGENT_TASKS and not SIMPLE_AGENT_TASKS[task_key].done():
        await event.respond("You already have a content creation task running. Please wait for it to complete.")
        return
    
    await event.respond(f"🤖 Creating content...\n\n📁 Project: {project_id}\n📝 Topic: {topic}\n🎯 Strategy: {strategy_name}")
    
    # Create and run task
    task = asyncio.create_task(
        run_simple_content_creation(event, user_id, project_id, topic, strategy_name)
    )
    SIMPLE_AGENT_TASKS[task_key] = task

async def run_simple_content_creation(event, user_id: int, project_id: str, topic: str, strategy_name: str):
    """Run simple content creation process"""
    try:
        # Get or create agent for project
        if project_id not in SIMPLE_AGENT_INSTANCES:
            SIMPLE_AGENT_INSTANCES[project_id] = await create_simple_ai_agent(project_id)
        
        agent = SIMPLE_AGENT_INSTANCES[project_id]
        
        await event.respond(f"📋 Generating content plan for '{topic}'...")
        
        # Generate content plan
        plan = await agent.generate_content_plan(topic, strategy_name)
        
        if not plan:
            await event.respond("❌ Failed to generate content plan. Make sure the strategy exists.")
            return
        
        await event.respond(f"🎬 Creating content: {plan.title}")
        
        # Create content
        result = await agent.create_content(plan)
        
        if result:
            result_message = f"""
🎉 **Content Creation Complete!**

📝 **Title:** {plan.title}
📋 **Description:** {plan.description}
⏱️ **Duration:** {plan.duration} seconds
🏷️ **Hashtags:** {' '.join(plan.hashtags[:3])}

📊 **Expected Performance:**
• Views: {plan.expected_performance.get('views', 'N/A'):,}
• Likes: {plan.expected_performance.get('likes', 'N/A'):,}
• Shares: {plan.expected_performance.get('shares', 'N/A'):,}

✅ Content has been created and is ready for review!
"""
            await event.respond(result_message)
        else:
            await event.respond("❌ Content creation failed. Please check the logs.")
            
    except Exception as e:
        logger.error(f"Error in content creation: {e}")
        await event.respond(f"❌ An error occurred during content creation: {str(e)}")
    
    finally:
        # Clean up task
        task_key = f"{user_id}_{project_id}"
        if task_key in SIMPLE_AGENT_TASKS:
            del SIMPLE_AGENT_TASKS[task_key]

async def handle_list_strategies(event, args: List[str]):
    """Handle listing strategies"""
    if len(args) < 1:
        await event.respond("Usage: /ai strategies [project]\nExample: /ai strategies my_project")
        return
    
    project_id = args[0]
    
    try:
        # Get or create agent for project
        if project_id not in SIMPLE_AGENT_INSTANCES:
            SIMPLE_AGENT_INSTANCES[project_id] = await create_simple_ai_agent(project_id)
        
        agent = SIMPLE_AGENT_INSTANCES[project_id]
        strategies = agent.get_strategies()
        
        if strategies:
            strategies_message = f"📚 **Strategies for Project: {project_id}**\n\n"
            
            for i, strategy in enumerate(strategies, 1):
                strategies_message += f"""
**{i}. {strategy['name']}**
📋 {strategy['description']}
📊 Type: {strategy['content_type']}
⏱️ Duration: {strategy['duration_range']['min']}-{strategy['duration_range']['max']}s
💰 Revenue: ${strategy['monetization_strategy']['target_revenue_per_1k_views']}/1K views
📅 Created: {strategy['created_at'][:10]}

"""
            
            strategies_message += f"\n💡 Use `/ai create {project_id} [topic] [strategy]` to create content!"
            await event.respond(strategies_message)
        else:
            await event.respond(f"❌ No strategies found for project '{project_id}'. Use `/ai learn {project_id} [strategy_name] [instructions]` to create one.")
            
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        await event.respond(f"❌ Error listing strategies: {str(e)}")

async def handle_generate_plan(event, args: List[str]):
    """Handle content plan generation"""
    if len(args) < 3:
        await event.respond("Usage: /ai plan [project] [topic] [strategy]\nExample: /ai plan my_project 'Ancient Egyptian secrets' hook_strategy")
        return
    
    project_id = args[0]
    topic = args[1]
    strategy_name = args[2]
    
    try:
        # Get or create agent for project
        if project_id not in SIMPLE_AGENT_INSTANCES:
            SIMPLE_AGENT_INSTANCES[project_id] = await create_simple_ai_agent(project_id)
        
        agent = SIMPLE_AGENT_INSTANCES[project_id]
        
        await event.respond(f"📋 Generating content plan for '{topic}'...")
        
        # Generate plan
        plan = await agent.generate_content_plan(topic, strategy_name)
        
        if plan:
            plan_message = f"""
📋 **Content Plan Generated**

📝 **Title:** {plan.title}
📋 **Description:** {plan.description}
⏱️ **Duration:** {plan.duration} seconds
🏷️ **Hashtags:** {' '.join(plan.hashtags)}

📊 **Expected Performance:**
• Views: {plan.expected_performance.get('views', 'N/A'):,}
• Likes: {plan.expected_performance.get('likes', 'N/A'):,}
• Shares: {plan.expected_performance.get('shares', 'N/A'):,}

💡 Use `/ai create {project_id} {topic} {strategy_name}` to create this content!
"""
            await event.respond(plan_message)
        else:
            await event.respond("❌ Failed to generate content plan. Make sure the strategy exists.")
            
    except Exception as e:
        logger.error(f"Error generating plan: {e}")
        await event.respond(f"❌ Error generating plan: {str(e)}")

async def handle_update_performance(event, args: List[str]):
    """Handle performance update"""
    if len(args) < 3:
        await event.respond("Usage: /ai performance [project] [strategy] [metrics]\nExample: /ai performance my_project hook_strategy 'views:50000,likes:2500,shares:500'")
        return
    
    project_id = args[0]
    strategy_name = args[1]
    metrics_str = " ".join(args[2:])
    
    try:
        # Parse metrics
        metrics = {}
        for item in metrics_str.split(','):
            if ':' in item:
                key, value = item.split(':', 1)
                try:
                    metrics[key.strip()] = int(value.strip())
                except ValueError:
                    metrics[key.strip()] = value.strip()
        
        # Get or create agent for project
        if project_id not in SIMPLE_AGENT_INSTANCES:
            SIMPLE_AGENT_INSTANCES[project_id] = await create_simple_ai_agent(project_id)
        
        agent = SIMPLE_AGENT_INSTANCES[project_id]
        
        await event.respond(f"📊 Updating performance for strategy '{strategy_name}'...")
        
        # Update performance (using a placeholder content title)
        analysis = await agent.update_performance(strategy_name, "Recent Content", metrics)
        
        if analysis:
            analysis_message = f"""
📊 **Performance Analysis Complete**

🎯 **Strategy:** {strategy_name}
📈 **Performance Score:** {analysis.get('performance_score', 'N/A')}

✅ **Strengths:**
{chr(10).join(f'• {strength}' for strength in analysis.get('strengths', []))}

⚠️ **Weaknesses:**
{chr(10).join(f'• {weakness}' for weakness in analysis.get('weaknesses', []))}

💡 **Improvements:**
{chr(10).join(f'• {improvement}' for improvement in analysis.get('improvements', []))}

The AI has learned from this performance data!
"""
            await event.respond(analysis_message)
        else:
            await event.respond("❌ Failed to update performance data.")
            
    except Exception as e:
        logger.error(f"Error updating performance: {e}")
        await event.respond(f"❌ Error updating performance: {str(e)}")

async def handle_view_history(event, args: List[str]):
    """Handle viewing performance history"""
    if len(args) < 1:
        await event.respond("Usage: /ai history [project] [strategy]\nExample: /ai history my_project hook_strategy")
        return
    
    project_id = args[0]
    strategy_name = args[1] if len(args) > 1 else None
    
    try:
        # Get or create agent for project
        if project_id not in SIMPLE_AGENT_INSTANCES:
            SIMPLE_AGENT_INSTANCES[project_id] = await create_simple_ai_agent(project_id)
        
        agent = SIMPLE_AGENT_INSTANCES[project_id]
        
        # Get performance history
        history = agent.get_performance_history(strategy_name)
        
        if history:
            history_message = f"📊 **Performance History for Project: {project_id}**\n\n"
            
            for i, entry in enumerate(history[:5], 1):  # Show last 5 entries
                metrics = entry['metrics']
                history_message += f"""
**{i}. {entry['content_title']}** ({entry['strategy_name']})
📈 Views: {metrics.get('views', 'N/A'):,}
👍 Likes: {metrics.get('likes', 'N/A'):,}
🔄 Shares: {metrics.get('shares', 'N/A'):,}
📅 Date: {entry['created_at'][:10]}

"""
            
            if len(history) > 5:
                history_message += f"\n... and {len(history) - 5} more entries"
            
            await event.respond(history_message)
        else:
            await event.respond(f"❌ No performance history found for project '{project_id}'.")
            
    except Exception as e:
        logger.error(f"Error viewing history: {e}")
        await event.respond(f"❌ Error viewing history: {str(e)}")

async def handle_export_data(event, args: List[str]):
    """Handle data export"""
    if len(args) < 1:
        await event.respond("Usage: /ai export [project]\nExample: /ai export my_project")
        return
    
    project_id = args[0]
    
    try:
        # Get or create agent for project
        if project_id not in SIMPLE_AGENT_INSTANCES:
            SIMPLE_AGENT_INSTANCES[project_id] = await create_simple_ai_agent(project_id)
        
        agent = SIMPLE_AGENT_INSTANCES[project_id]
        
        # Export data
        data = agent.export_project_data()
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_data_{project_id}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        await event.respond(f"📊 Project data exported to {filename}")
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        await event.respond(f"❌ Error exporting data: {str(e)}")

# Integration with existing bot
def register_simple_ai_handlers():
    """Register simple AI agent handlers with the existing bot"""
    
    @bot.on(events.NewMessage(pattern='/ai'))
    async def simple_ai_handler(event):
        """Handle simple AI agent commands"""
        command_parts = event.text.strip().split()
        await handle_simple_ai_command(event, command_parts)

# Export functions for use in main bot
__all__ = [
    'handle_simple_ai_command',
    'register_simple_ai_handlers',
    'SIMPLE_AGENT_INSTANCES',
    'SIMPLE_AGENT_TASKS'
] 