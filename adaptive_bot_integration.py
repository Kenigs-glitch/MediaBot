import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

from adaptive_ai_agent import AdaptiveTikTokAIAgent, create_adaptive_ai_agent
from bot import bot, is_authorized, show_initial_menu

# Adaptive AI Agent integration state
ADAPTIVE_AGENT_STATE = {}
ADAPTIVE_AGENT_TASKS = {}
ADAPTIVE_AGENT_INSTANCES = {}

async def handle_adaptive_ai_command(event, command_parts: List[str]):
    """Handle adaptive AI agent commands from Telegram bot"""
    user = await event.get_sender()
    user_id = user.id
    
    if not is_authorized(user_id):
        await event.respond("You are not authorized to use adaptive AI agent commands.")
        return
    
    if len(command_parts) < 2:
        await show_adaptive_ai_help(event)
        return
    
    subcommand = command_parts[1].lower()
    
    try:
        if subcommand == "learn":
            await handle_learn_strategy(event, command_parts[2:])
        elif subcommand == "create":
            await handle_adaptive_create(event, command_parts[2:])
        elif subcommand == "strategies":
            await handle_list_strategies(event)
        elif subcommand == "plan":
            await handle_adaptive_plan(event, command_parts[2:])
        elif subcommand == "performance":
            await handle_performance_update(event, command_parts[2:])
        elif subcommand == "status":
            await handle_adaptive_status(event, user_id)
        elif subcommand == "stop":
            await handle_stop_adaptive_agent(event, user_id)
        elif subcommand == "export":
            await handle_export_data(event, user_id)
        else:
            await show_adaptive_ai_help(event)
            
    except Exception as e:
        logger.error(f"Error in adaptive AI agent command: {e}")
        await event.respond(f"An error occurred: {str(e)}")

async def show_adaptive_ai_help(event):
    """Show adaptive AI agent help menu"""
    help_text = """
🧠 **Adaptive AI Agent Commands**

/ai learn [instructions] - Learn new strategy from your instructions
/ai create [topic] [strategy] - Create content using learned strategy
/ai strategies - List all available strategies (base + learned)
/ai plan [topic] [strategy] - Generate content plan for strategy
/ai performance [strategy] [metrics] - Update strategy performance
/ai status - Check adaptive AI agent status
/ai stop - Stop running adaptive AI tasks
/ai export - Export learning data and strategies

**Learning Examples:**
/ai learn "Create 10-second hooks leading to 2-minute deep dives for maximum creator rewards"
/ai learn "Educational content with progressive difficulty from basics to masterclass"
/ai learn "Historical documentaries with period-accurate visuals and investigative approach"

**Content Creation Examples:**
/ai create "Ancient Egyptian secrets" hybrid_hook_payoff
/ai create "Cooking masterclass" knowledge_ladder
/ai create "World War II mysteries" ai_history_documentary

**Performance Update Example:**
/ai performance hybrid_hook_payoff "views:50000,likes:2500,shares:500"
"""
    await event.respond(help_text)

async def handle_learn_strategy(event, args: List[str]):
    """Handle strategy learning from user instructions"""
    user = await event.get_sender()
    user_id = user.id
    
    if not args:
        await event.respond("Usage: /ai learn [instructions]\nExample: /ai learn 'Create 10-second hooks leading to 2-minute deep dives for maximum creator rewards'")
        return
    
    instructions = " ".join(args)
    
    await event.respond(f"🧠 Learning new strategy from your instructions...\n\n📝 Instructions: {instructions}")
    
    try:
        # Get or create adaptive agent for user
        if user_id not in ADAPTIVE_AGENT_INSTANCES:
            ADAPTIVE_AGENT_INSTANCES[user_id] = await create_adaptive_ai_agent()
        
        agent = ADAPTIVE_AGENT_INSTANCES[user_id]
        
        # Learn from instructions
        learning_result = await agent.learn_from_user_instructions(user_id, instructions)
        
        if learning_result['status'] == 'success':
            strategy_name = learning_result['strategy']
            analysis = learning_result['analysis']
            
            # Update state
            ADAPTIVE_AGENT_STATE[user_id] = {
                'status': 'learned',
                'strategy': strategy_name,
                'instructions': instructions,
                'analysis': analysis,
                'learned_at': datetime.now().isoformat()
            }
            
            result_message = f"""
✅ **Strategy Learning Complete!**

🎯 **New Strategy:** {strategy_name}
📊 **Content Type:** {analysis.get('content_type', 'adaptive')}
⏱️ **Duration Range:** {analysis.get('target_duration', {}).get('min', 'N/A')}-{analysis.get('target_duration', {}).get('max', 'N/A')} seconds
🎭 **Viral Formula:** {analysis.get('viral_formula', 'N/A')}
💰 **Monetization Focus:** {analysis.get('monetization_focus', 'N/A')}

🧠 **AI Analysis:**
• Target Audience: {analysis.get('target_audience', 'N/A')}
• Psychological Triggers: {', '.join(analysis.get('psychological_triggers', []))}
• Content Mix: {json.dumps(analysis.get('content_mix', {}), indent=2)}

💡 **Next Steps:**
Use `/ai create [topic] {strategy_name}` to create content with this strategy!
"""
            await event.respond(result_message)
        else:
            await event.respond(f"❌ Failed to learn strategy: {learning_result.get('message', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error learning strategy: {e}")
        await event.respond(f"❌ Error learning strategy: {str(e)}")

async def handle_adaptive_create(event, args: List[str]):
    """Handle adaptive content creation"""
    user = await event.get_sender()
    user_id = user.id
    
    if len(args) < 1:
        await event.respond("Usage: /ai create [topic] [strategy]\nExample: /ai create 'Ancient Egyptian secrets' hybrid_hook_payoff")
        return
    
    topic = args[0]
    strategy_name = args[1] if len(args) > 1 else None
    
    # Check if user has learned strategies
    if user_id not in ADAPTIVE_AGENT_INSTANCES:
        await event.respond("❌ No adaptive AI agent found. Use `/ai learn [instructions]` first to teach the AI your strategy.")
        return
    
    # Check if user already has a running task
    if user_id in ADAPTIVE_AGENT_TASKS and not ADAPTIVE_AGENT_TASKS[user_id].done():
        await event.respond("You already have a content creation task running. Use `/ai stop` to cancel it first.")
        return
    
    await event.respond(f"🧠 Creating adaptive content...\n📝 Topic: {topic}\n🎯 Strategy: {strategy_name or 'Auto-selected'}")
    
    # Create and run adaptive AI agent task
    task = asyncio.create_task(
        run_adaptive_content_creation(event, user_id, topic, strategy_name)
    )
    ADAPTIVE_AGENT_TASKS[user_id] = task
    
    # Store state
    ADAPTIVE_AGENT_STATE[user_id] = {
        'status': 'creating',
        'topic': topic,
        'strategy': strategy_name,
        'start_time': datetime.now(),
        'progress': 0
    }

async def run_adaptive_content_creation(event, user_id: int, topic: str, strategy_name: Optional[str]):
    """Run adaptive content creation process"""
    try:
        agent = ADAPTIVE_AGENT_INSTANCES[user_id]
        
        await update_adaptive_status(event, user_id, "Generating adaptive content plan...", 30)
        
        # Generate content plan
        plan = await agent.generate_adaptive_content_plan(user_id, topic, strategy_name)
        
        if not plan:
            await event.respond("❌ Failed to generate content plan. Please try again.")
            return
        
        await update_adaptive_status(event, user_id, "Creating adaptive content...", 70)
        
        # Create content
        content_result = await agent.create_adaptive_content(plan)
        
        if content_result:
            await update_adaptive_status(event, user_id, "✅ Adaptive content creation completed!", 100)
            
            # Send results
            result_message = f"""
🎉 **Adaptive Content Creation Complete!**

📝 **Title:** {plan.title}
📋 **Description:** {plan.description}
🎯 **Content Type:** {plan.content_type}
⏱️ **Duration:** {plan.duration} seconds
🏷️ **Hashtags:** {' '.join(plan.hashtags[:3])}
📊 **Expected Views:** {plan.expected_performance.get('views', 'N/A'):,}

💰 **Monetization Strategy:**
• Primary: {plan.monetization_strategy.get('primary', 'N/A')}
• Secondary: {plan.monetization_strategy.get('secondary', 'N/A')}

📈 **Posting Schedule:** {json.dumps(plan.posting_schedule, indent=2)}

The adaptive content has been created and is ready for review!
"""
            await event.respond(result_message)
            
            # Update state
            ADAPTIVE_AGENT_STATE[user_id] = {
                'status': 'completed',
                'topic': topic,
                'strategy': strategy_name,
                'completion_time': datetime.now(),
                'plan': plan.__dict__,
                'result': content_result
            }
        else:
            await event.respond("❌ Adaptive content creation failed. Please check the logs and try again.")
            ADAPTIVE_AGENT_STATE[user_id]['status'] = 'failed'
            
    except Exception as e:
        logger.error(f"Error in adaptive content creation: {e}")
        await event.respond(f"❌ An error occurred during adaptive content creation: {str(e)}")
        ADAPTIVE_AGENT_STATE[user_id]['status'] = 'error'
        ADAPTIVE_AGENT_STATE[user_id]['error'] = str(e)
    
    finally:
        # Clean up task
        if user_id in ADAPTIVE_AGENT_TASKS:
            del ADAPTIVE_AGENT_TASKS[user_id]

async def handle_list_strategies(event):
    """Handle listing all available strategies"""
    user = await event.get_sender()
    user_id = user.id
    
    try:
        # Get or create adaptive agent for user
        if user_id not in ADAPTIVE_AGENT_INSTANCES:
            ADAPTIVE_AGENT_INSTANCES[user_id] = await create_adaptive_ai_agent()
        
        agent = ADAPTIVE_AGENT_INSTANCES[user_id]
        strategies = agent.get_available_strategies()
        
        if strategies:
            strategies_message = "📚 **Available Strategies:**\n\n"
            
            # Group by type
            base_strategies = {k: v for k, v in strategies.items() if v['type'] == 'base'}
            custom_strategies = {k: v for k, v in strategies.items() if v['type'] == 'custom'}
            
            if base_strategies:
                strategies_message += "🔧 **Base Strategies:**\n"
                for name, strategy in base_strategies.items():
                    strategies_message += f"""
• **{name}** ({strategy['content_type']})
  {strategy['description']}
  Duration: {strategy['duration_range'][0]}-{strategy['duration_range'][1]}s
  Revenue: ${strategy['monetization_potential']:.2f}/1K views

"""
            
            if custom_strategies:
                strategies_message += "🧠 **Learned Strategies:**\n"
                for name, strategy in custom_strategies.items():
                    strategies_message += f"""
• **{name}** ({strategy['content_type']})
  {strategy['description']}
  Duration: {strategy['duration_range'][0]}-{strategy['duration_range'][1]}s
  Revenue: ${strategy['monetization_potential']:.2f}/1K views

"""
            
            strategies_message += "\n💡 Use `/ai create [topic] [strategy]` to create content with any strategy!"
            await event.respond(strategies_message)
        else:
            await event.respond("❌ No strategies available.")
            
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        await event.respond(f"❌ Error listing strategies: {str(e)}")

async def handle_adaptive_plan(event, args: List[str]):
    """Handle adaptive content plan generation"""
    user = await event.get_sender()
    user_id = user.id
    
    if len(args) < 1:
        await event.respond("Usage: /ai plan [topic] [strategy]\nExample: /ai plan 'Ancient Egyptian secrets' hybrid_hook_payoff")
        return
    
    topic = args[0]
    strategy_name = args[1] if len(args) > 1 else None
    
    try:
        # Get or create adaptive agent for user
        if user_id not in ADAPTIVE_AGENT_INSTANCES:
            ADAPTIVE_AGENT_INSTANCES[user_id] = await create_adaptive_ai_agent()
        
        agent = ADAPTIVE_AGENT_INSTANCES[user_id]
        
        await event.respond(f"🧠 Generating adaptive content plan for '{topic}'...")
        
        # Generate plan
        plan = await agent.generate_adaptive_content_plan(user_id, topic, strategy_name)
        
        if plan:
            plan_message = f"""
📋 **Adaptive Content Plan**

📝 **Title:** {plan.title}
📋 **Description:** {plan.description}
🎯 **Content Type:** {plan.content_type}
⏱️ **Duration:** {plan.duration} seconds
🏷️ **Hashtags:** {' '.join(plan.hashtags)}

💰 **Monetization Strategy:**
• Primary: {plan.monetization_strategy.get('primary', 'N/A')}
• Secondary: {plan.monetization_strategy.get('secondary', 'N/A')}

📊 **Expected Performance:**
• Views: {plan.expected_performance.get('views', 'N/A'):,}
• Likes: {plan.expected_performance.get('likes', 'N/A'):,}
• Shares: {plan.expected_performance.get('shares', 'N/A'):,}

📅 **Posting Schedule:** {json.dumps(plan.posting_schedule, indent=2)}

💡 Use `/ai create {topic} {strategy_name or 'auto'}` to create this content!
"""
            await event.respond(plan_message)
        else:
            await event.respond("❌ Failed to generate adaptive content plan.")
            
    except Exception as e:
        logger.error(f"Error generating adaptive plan: {e}")
        await event.respond(f"❌ Error generating adaptive plan: {str(e)}")

async def handle_performance_update(event, args: List[str]):
    """Handle performance update for strategy learning"""
    user = await event.get_sender()
    user_id = user.id
    
    if len(args) < 2:
        await event.respond("Usage: /ai performance [strategy] [metrics]\nExample: /ai performance hybrid_hook_payoff 'views:50000,likes:2500,shares:500'")
        return
    
    strategy_name = args[0]
    metrics_str = " ".join(args[1:])
    
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
        
        # Get or create adaptive agent for user
        if user_id not in ADAPTIVE_AGENT_INSTANCES:
            ADAPTIVE_AGENT_INSTANCES[user_id] = await create_adaptive_ai_agent()
        
        agent = ADAPTIVE_AGENT_INSTANCES[user_id]
        
        await event.respond(f"📊 Updating performance for strategy '{strategy_name}'...")
        
        # Update performance
        analysis = await agent.update_strategy_performance(strategy_name, metrics)
        
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

🔄 **Strategy Adjustments:**
{json.dumps(analysis.get('strategy_adjustments', {}), indent=2)}

The AI has learned from this performance data and will improve future content!
"""
            await event.respond(analysis_message)
        else:
            await event.respond("❌ Failed to update performance data.")
            
    except Exception as e:
        logger.error(f"Error updating performance: {e}")
        await event.respond(f"❌ Error updating performance: {str(e)}")

async def handle_adaptive_status(event, user_id: int):
    """Handle adaptive agent status check"""
    if user_id not in ADAPTIVE_AGENT_STATE:
        await event.respond("🧠 No adaptive AI agent activity found for your account.")
        return
    
    state = ADAPTIVE_AGENT_STATE[user_id]
    
    status_message = f"""
🧠 **Adaptive AI Agent Status**

📊 **Status:** {state['status'].title()}
🎯 **Strategy:** {state.get('strategy', 'N/A')}
📝 **Topic:** {state.get('topic', 'N/A')}
⏰ **Started:** {state.get('start_time', 'N/A')}

"""
    
    if state['status'] == 'creating':
        progress = state.get('progress', 0)
        status_message += f"📈 **Progress:** {progress}%"
        
        # Check if task is running
        if user_id in ADAPTIVE_AGENT_TASKS and not ADAPTIVE_AGENT_TASKS[user_id].done():
            status_message += "\n🔄 **Task:** Running"
        else:
            status_message += "\n⏸️ **Task:** Paused"
    
    elif state['status'] == 'learned':
        learned_at = state.get('learned_at', 'N/A')
        strategy = state.get('strategy', 'N/A')
        status_message += f"✅ **Learned Strategy:** {strategy}\n📚 **Learned At:** {learned_at}"
    
    elif state['status'] == 'completed':
        completion_time = state.get('completion_time', 'N/A')
        status_message += f"✅ **Completed:** {completion_time}"
    
    elif state['status'] == 'failed':
        error = state.get('error', 'Unknown error')
        status_message += f"❌ **Error:** {error}"
    
    await event.respond(status_message)

async def handle_stop_adaptive_agent(event, user_id: int):
    """Handle stopping adaptive AI agent tasks"""
    if user_id in ADAPTIVE_AGENT_TASKS:
        task = ADAPTIVE_AGENT_TASKS[user_id]
        if not task.done():
            task.cancel()
            await event.respond("🛑 Adaptive AI agent task cancelled.")
        else:
            await event.respond("ℹ️ No running adaptive AI agent tasks found.")
    else:
        await event.respond("ℹ️ No adaptive AI agent tasks found for your account.")

async def handle_export_data(event, user_id: int):
    """Handle exporting learning data"""
    try:
        if user_id not in ADAPTIVE_AGENT_INSTANCES:
            await event.respond("❌ No adaptive AI agent found for your account.")
            return
        
        agent = ADAPTIVE_AGENT_INSTANCES[user_id]
        data = agent.export_learning_data()
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"adaptive_ai_data_{user_id}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        await event.respond(f"📊 Learning data exported to {filename}")
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        await event.respond(f"❌ Error exporting data: {str(e)}")

async def update_adaptive_status(event, user_id: int, message: str, progress: int):
    """Update adaptive AI agent status and progress"""
    if user_id in ADAPTIVE_AGENT_STATE:
        ADAPTIVE_AGENT_STATE[user_id]['progress'] = progress
    
    # Send progress update
    progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
    status_message = f"🧠 {message}\n📊 [{progress_bar}] {progress}%"
    
    await event.respond(status_message)

# Integration with existing bot
def register_adaptive_ai_handlers():
    """Register adaptive AI agent handlers with the existing bot"""
    
    @bot.on(events.NewMessage(pattern='/ai'))
    async def adaptive_ai_handler(event):
        """Handle adaptive AI agent commands"""
        command_parts = event.text.strip().split()
        await handle_adaptive_ai_command(event, command_parts)

# Export functions for use in main bot
__all__ = [
    'handle_adaptive_ai_command',
    'register_adaptive_ai_handlers',
    'ADAPTIVE_AGENT_STATE',
    'ADAPTIVE_AGENT_TASKS',
    'ADAPTIVE_AGENT_INSTANCES'
] 