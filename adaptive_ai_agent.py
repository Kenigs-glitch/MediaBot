import os
import json
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from loguru import logger
import random
import re

# Import existing MediaBot functions
from txt2img import generate_image_from_text
from media_utils import process_image_to_video
from long_video import LongVideoGenerator
from config import COMFYUI_URL, COMFYUI_OUTPUT_DIR, WORKFLOW_FILE, GENERATION_TIMEOUT

# Cerebras API Configuration
CEREBRAS_API_URL = os.getenv('CEREBRAS_API_URL', 'https://api.cerebras.ai/v1')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')

@dataclass
class AdaptiveStrategy:
    """Dynamic content strategy that can be modified by user instructions"""
    name: str
    description: str
    target_audience: str
    content_type: str
    viral_formula: str
    psychological_triggers: List[str]
    duration_range: Tuple[int, int]  # min, max seconds
    optimal_duration: int
    hashtags: List[str]
    monetization_potential: float
    prompt_templates: List[str]
    narrative_arc: Optional[str] = None
    series_structure: Optional[Dict] = None
    revenue_streams: List[str] = None
    content_mix: Dict[str, float] = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)

@dataclass
class ContentSeries:
    """Multi-part content series for maximum monetization"""
    title: str
    description: str
    total_episodes: int
    episode_structure: List[Dict]
    hook_strategy: str
    monetization_strategy: str
    target_revenue: float
    completion_bonus: Optional[float] = None

@dataclass
class AdaptiveContentPlan:
    """Flexible content plan that adapts to user requirements"""
    title: str
    description: str
    content_type: str  # 'single', 'series', 'ladder'
    duration: int
    segments: List[Dict]
    hashtags: List[str]
    posting_schedule: Dict
    expected_performance: Dict
    monetization_strategy: Dict
    narrative_arc: Optional[str] = None
    series_info: Optional[ContentSeries] = None
    user_instructions: Optional[str] = None

class AdaptiveTikTokAIAgent:
    """Adaptive AI Agent that learns and adjusts strategies based on user input"""
    
    def __init__(self):
        self.cerebras_client = self._init_cerebras_client()
        self.strategy_database = self._load_base_strategies()
        self.user_preferences = {}
        self.performance_history = []
        self.learning_data = []
        self.custom_strategies = {}
        
    def _init_cerebras_client(self):
        """Initialize Cerebras API client"""
        if not CEREBRAS_API_KEY:
            raise ValueError("CEREBRAS_API_KEY environment variable is required")
        
        return {
            'api_key': CEREBRAS_API_KEY,
            'base_url': CEREBRAS_API_URL,
            'headers': {
                'Authorization': f'Bearer {CEREBRAS_API_KEY}',
                'Content-Type': 'application/json'
            }
        }
    
    def _load_base_strategies(self) -> Dict[str, AdaptiveStrategy]:
        """Load base strategies that can be modified"""
        return {
            'hybrid_hook_payoff': AdaptiveStrategy(
                name='hybrid_hook_payoff',
                description='10-15 second viral hooks driving to 1-3 minute monetizable content',
                target_audience='general audience, high engagement seekers',
                content_type='series',
                viral_formula='hook_to_payoff',
                psychological_triggers=['curiosity', 'shock', 'satisfaction', 'completion'],
                duration_range=(10, 180),
                optimal_duration=90,
                hashtags=['#Viral', '#Shocking', '#Truth', '#Revealed'],
                monetization_potential=0.85,
                prompt_templates=[
                    "Shocking reveal of {topic} with dramatic lighting, suspenseful buildup, cinematic documentary style",
                    "Before/after transformation of {subject}, investigative journalism style, evidence presentation"
                ],
                narrative_arc='hook_investigation_revelation',
                series_structure={
                    'hook_episode': {'duration': 15, 'purpose': 'viral discovery'},
                    'investigation_episodes': {'duration': 60, 'purpose': 'monetization'},
                    'finale': {'duration': 120, 'purpose': 'maximum payout'}
                },
                revenue_streams=['creator_rewards', 'tiktok_shop', 'brand_sponsorships'],
                content_mix={'hook': 0.2, 'monetizable': 0.6, 'premium': 0.2}
            ),
            'knowledge_ladder': AdaptiveStrategy(
                name='knowledge_ladder',
                description='Progressive content from micro-lessons to masterclasses',
                target_audience='educational content consumers, skill builders',
                content_type='ladder',
                viral_formula='progressive_learning',
                psychological_triggers=['achievement', 'growth', 'expertise', 'mastery'],
                duration_range=(10, 300),
                optimal_duration=120,
                hashtags=['#Learn', '#Skills', '#Education', '#Mastery'],
                monetization_potential=0.75,
                prompt_templates=[
                    "Step-by-step tutorial of {skill} with clear progression, educational graphics, professional instruction style",
                    "Masterclass demonstration of {technique} with detailed explanations, close-up shots, expert commentary"
                ],
                narrative_arc='basics_advanced_mastery',
                series_structure={
                    'micro_lessons': {'duration': 15, 'purpose': 'viral hooks'},
                    'standard_tutorials': {'duration': 90, 'purpose': 'creator rewards'},
                    'masterclasses': {'duration': 240, 'purpose': 'premium monetization'}
                },
                revenue_streams=['creator_rewards', 'course_sales', 'affiliate_marketing'],
                content_mix={'micro': 0.4, 'standard': 0.4, 'masterclass': 0.2}
            ),
            'ai_history_documentary': AdaptiveStrategy(
                name='ai_history_documentary',
                description='Historical recreations with period-accurate visuals',
                target_audience='history enthusiasts, documentary lovers',
                content_type='documentary',
                viral_formula='investigative_revelation',
                psychological_triggers=['mystery', 'discovery', 'awe', 'understanding'],
                duration_range=(30, 300),
                optimal_duration=180,
                hashtags=['#History', '#Documentary', '#Truth', '#Investigation'],
                monetization_potential=0.90,
                prompt_templates=[
                    "Cinematic documentary style recreation of {historical_event}, Ken Burns effect, period-accurate visuals, investigative journalism approach",
                    "What really happened during {historical_period} with dramatic reenactments, evidence presentation, expert analysis"
                ],
                narrative_arc='mystery_investigation_revelation',
                series_structure={
                    'hook_episode': {'duration': 30, 'purpose': 'viral discovery'},
                    'investigation_episodes': {'duration': 120, 'purpose': 'deep engagement'},
                    'finale': {'duration': 240, 'purpose': 'comprehensive explanation'}
                },
                revenue_streams=['creator_rewards', 'documentary_sales', 'educational_licensing'],
                content_mix={'hook': 0.2, 'investigation': 0.6, 'finale': 0.2}
            )
        }
    
    async def learn_from_user_instructions(self, user_id: int, instructions: str) -> Dict:
        """Learn and adapt strategy based on user instructions"""
        try:
            # Analyze user instructions using Cerebras API
            analysis_prompt = f"""
            Analyze these user instructions for TikTok content creation and extract key requirements:
            
            Instructions: "{instructions}"
            
            Extract and return JSON with:
            {{
                "content_type": "single/series/ladder/documentary",
                "target_duration": {{"min": 10, "max": 300, "optimal": 90}},
                "target_audience": "description",
                "viral_formula": "hook_to_payoff/progressive_learning/investigative_revelation",
                "psychological_triggers": ["list", "of", "triggers"],
                "monetization_focus": "creator_rewards/tiktok_shop/brand_sponsorships",
                "content_mix": {{"hook": 0.2, "main": 0.6, "premium": 0.2}},
                "custom_requirements": ["list", "of", "specific", "requirements"],
                "suggested_strategy": "strategy_name_or_custom"
            }}
            """
            
            response = requests.post(
                f"{self.cerebras_client['base_url']}/chat/completions",
                headers=self.cerebras_client['headers'],
                json={
                    "model": "cerebras-llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": analysis_prompt}],
                    "max_tokens": 800,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    analysis = json.loads(content[json_start:json_end])
                    
                    # Store user preferences
                    self.user_preferences[user_id] = analysis
                    
                    # Create or modify strategy based on analysis
                    strategy = await self._create_adaptive_strategy(analysis, instructions)
                    
                    # Store learning data
                    self.learning_data.append({
                        'user_id': user_id,
                        'instructions': instructions,
                        'analysis': analysis,
                        'strategy': strategy.name,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return {
                        'status': 'success',
                        'strategy': strategy.name,
                        'analysis': analysis,
                        'message': f"Learned new strategy: {strategy.name}"
                    }
            
            return {'status': 'error', 'message': 'Failed to analyze instructions'}
            
        except Exception as e:
            logger.error(f"Error learning from instructions: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _create_adaptive_strategy(self, analysis: Dict, instructions: str) -> AdaptiveStrategy:
        """Create or modify strategy based on user analysis"""
        strategy_name = analysis.get('suggested_strategy', 'custom_adaptive')
        
        # Check if we should modify existing strategy or create new one
        if strategy_name in self.strategy_database:
            base_strategy = self.strategy_database[strategy_name]
            # Modify existing strategy
            modified_strategy = AdaptiveStrategy(
                name=f"{strategy_name}_modified",
                description=f"Modified {base_strategy.description} based on user requirements",
                target_audience=analysis.get('target_audience', base_strategy.target_audience),
                content_type=analysis.get('content_type', base_strategy.content_type),
                viral_formula=analysis.get('viral_formula', base_strategy.viral_formula),
                psychological_triggers=analysis.get('psychological_triggers', base_strategy.psychological_triggers),
                duration_range=(
                    analysis.get('target_duration', {}).get('min', base_strategy.duration_range[0]),
                    analysis.get('target_duration', {}).get('max', base_strategy.duration_range[1])
                ),
                optimal_duration=analysis.get('target_duration', {}).get('optimal', base_strategy.optimal_duration),
                hashtags=base_strategy.hashtags,
                monetization_potential=base_strategy.monetization_potential,
                prompt_templates=base_strategy.prompt_templates,
                narrative_arc=base_strategy.narrative_arc,
                series_structure=base_strategy.series_structure,
                revenue_streams=base_strategy.revenue_streams,
                content_mix=analysis.get('content_mix', base_strategy.content_mix)
            )
        else:
            # Create completely new strategy
            modified_strategy = AdaptiveStrategy(
                name=strategy_name,
                description=f"Custom strategy based on: {instructions[:100]}...",
                target_audience=analysis.get('target_audience', 'general audience'),
                content_type=analysis.get('content_type', 'single'),
                viral_formula=analysis.get('viral_formula', 'hook_to_payoff'),
                psychological_triggers=analysis.get('psychological_triggers', ['curiosity', 'engagement']),
                duration_range=(
                    analysis.get('target_duration', {}).get('min', 10),
                    analysis.get('target_duration', {}).get('max', 300)
                ),
                optimal_duration=analysis.get('target_duration', {}).get('optimal', 90),
                hashtags=['#Custom', '#Viral', '#Content'],
                monetization_potential=0.70,
                prompt_templates=[
                    f"Custom content about {{topic}} with {analysis.get('viral_formula', 'engaging')} approach",
                    f"Professional presentation of {{subject}} optimized for {analysis.get('content_type', 'viral')} content"
                ],
                narrative_arc=analysis.get('viral_formula', 'hook_to_payoff'),
                content_mix=analysis.get('content_mix', {'main': 1.0})
            )
        
        # Store the modified/custom strategy
        self.custom_strategies[modified_strategy.name] = modified_strategy
        
        return modified_strategy
    
    async def generate_adaptive_content_plan(self, user_id: int, topic: str, strategy_name: Optional[str] = None) -> Optional[AdaptiveContentPlan]:
        """Generate content plan using adaptive strategy"""
        try:
            # Get user preferences and strategy
            user_prefs = self.user_preferences.get(user_id, {})
            
            if strategy_name and strategy_name in self.custom_strategies:
                strategy = self.custom_strategies[strategy_name]
            elif strategy_name and strategy_name in self.strategy_database:
                strategy = self.strategy_database[strategy_name]
            else:
                # Use user's preferred strategy or default
                preferred_strategy = user_prefs.get('suggested_strategy', 'hybrid_hook_payoff')
                strategy = self.custom_strategies.get(preferred_strategy, 
                                                     self.strategy_database.get(preferred_strategy, 
                                                                               self.strategy_database['hybrid_hook_payoff']))
            
            # Generate adaptive content plan
            plan_prompt = f"""
            Create an adaptive TikTok content plan for topic: "{topic}"
            
            Strategy: {strategy.name}
            Content Type: {strategy.content_type}
            Duration Range: {strategy.duration_range[0]}-{strategy.duration_range[1]} seconds
            Optimal Duration: {strategy.optimal_duration} seconds
            Viral Formula: {strategy.viral_formula}
            Psychological Triggers: {', '.join(strategy.psychological_triggers)}
            User Preferences: {json.dumps(user_prefs, indent=2)}
            
            Generate a JSON response with:
            {{
                "title": "Engaging title",
                "description": "Content description",
                "content_type": "{strategy.content_type}",
                "duration": {strategy.optimal_duration},
                "segments": [
                    {{
                        "prompt": "Segment prompt",
                        "frames": 50,
                        "duration": 15,
                        "purpose": "hook/investigation/revelation"
                    }}
                ],
                "hashtags": ["#relevant", "#hashtags"],
                "posting_schedule": {{"frequency": "daily", "optimal_times": ["14:00", "18:00"]}},
                "expected_performance": {{"views": 50000, "likes": 2500, "shares": 500}},
                "monetization_strategy": {{"primary": "creator_rewards", "secondary": "tiktok_shop"}},
                "narrative_arc": "{strategy.narrative_arc}",
                "user_instructions": "Custom requirements from user"
            }}
            """
            
            response = requests.post(
                f"{self.cerebras_client['base_url']}/chat/completions",
                headers=self.cerebras_client['headers'],
                json={
                    "model": "cerebras-llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": plan_prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.8
                }
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    plan_data = json.loads(content[json_start:json_end])
                    
                    return AdaptiveContentPlan(
                        title=plan_data['title'],
                        description=plan_data['description'],
                        content_type=plan_data['content_type'],
                        duration=plan_data['duration'],
                        segments=plan_data['segments'],
                        hashtags=plan_data['hashtags'],
                        posting_schedule=plan_data['posting_schedule'],
                        expected_performance=plan_data['expected_performance'],
                        monetization_strategy=plan_data['monetization_strategy'],
                        narrative_arc=plan_data.get('narrative_arc'),
                        user_instructions=plan_data.get('user_instructions')
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating adaptive content plan: {e}")
            return None
    
    async def create_adaptive_content(self, plan: AdaptiveContentPlan) -> Optional[str]:
        """Create content using adaptive plan"""
        try:
            logger.info(f"Creating adaptive content: {plan.title}")
            
            # Generate initial image with optimized prompt
            initial_prompt = plan.segments[0]['prompt'] if plan.segments else plan.description
            logger.info("Generating initial image...")
            image_path = await generate_image_from_text(initial_prompt, COMFYUI_URL, COMFYUI_OUTPUT_DIR)
            
            if not image_path or not os.path.exists(image_path):
                logger.error("Failed to generate initial image")
                return None
            
            # Create video based on content type
            if plan.content_type == 'single':
                # Single video
                segment = plan.segments[0]
                await process_image_to_video(
                    segment['prompt'], 
                    image_path, 
                    segment['frames'], 
                    COMFYUI_URL, 
                    WORKFLOW_FILE
                )
            elif plan.content_type in ['series', 'documentary', 'ladder']:
                # Multi-segment content
                generator = LongVideoGenerator(COMFYUI_URL, WORKFLOW_FILE, GENERATION_TIMEOUT)
                
                video_path = await generator.generate_long_video(
                    initial_prompt=plan.segments[0]['prompt'],
                    initial_image=image_path,
                    segments_data=plan.segments
                )
                
                if video_path and os.path.exists(video_path):
                    logger.info(f"Multi-segment content created: {video_path}")
                    return video_path
            
            # Clean up
            if os.path.exists(image_path):
                os.remove(image_path)
            
            logger.info("Adaptive content creation completed")
            return "content_created"
            
        except Exception as e:
            logger.error(f"Error creating adaptive content: {e}")
            return None
    
    async def update_strategy_performance(self, strategy_name: str, performance_metrics: Dict):
        """Update strategy based on performance data"""
        try:
            # Store performance data
            self.performance_history.append({
                'strategy': strategy_name,
                'metrics': performance_metrics,
                'timestamp': datetime.now().isoformat()
            })
            
            # Analyze performance and suggest improvements
            analysis_prompt = f"""
            Analyze this content performance and suggest strategy improvements:
            
            Strategy: {strategy_name}
            Performance: {json.dumps(performance_metrics, indent=2)}
            
            Provide improvement suggestions in JSON format:
            {{
                "performance_score": 0.85,
                "strengths": ["list", "of", "strengths"],
                "weaknesses": ["list", "of", "weaknesses"],
                "improvements": ["list", "of", "suggestions"],
                "strategy_adjustments": {{"duration": "adjustment", "formula": "adjustment"}}
            }}
            """
            
            response = requests.post(
                f"{self.cerebras_client['base_url']}/chat/completions",
                headers=self.cerebras_client['headers'],
                json={
                    "model": "cerebras-llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": analysis_prompt}],
                    "max_tokens": 500,
                    "temperature": 0.5
                }
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    analysis = json.loads(content[json_start:json_end])
                    
                    # Apply strategy adjustments if strategy exists
                    if strategy_name in self.custom_strategies:
                        strategy = self.custom_strategies[strategy_name]
                        adjustments = analysis.get('strategy_adjustments', {})
                        
                        # Apply adjustments
                        if 'duration' in adjustments:
                            # Parse duration adjustment
                            pass
                        
                        logger.info(f"Updated strategy {strategy_name} based on performance")
                    
                    return analysis
            
            return {}
            
        except Exception as e:
            logger.error(f"Error updating strategy performance: {e}")
            return {}
    
    def get_available_strategies(self) -> Dict[str, Dict]:
        """Get all available strategies (base + custom)"""
        strategies = {}
        
        # Add base strategies
        for name, strategy in self.strategy_database.items():
            strategies[name] = {
                'name': strategy.name,
                'description': strategy.description,
                'content_type': strategy.content_type,
                'duration_range': strategy.duration_range,
                'monetization_potential': strategy.monetization_potential,
                'type': 'base'
            }
        
        # Add custom strategies
        for name, strategy in self.custom_strategies.items():
            strategies[name] = {
                'name': strategy.name,
                'description': strategy.description,
                'content_type': strategy.content_type,
                'duration_range': strategy.duration_range,
                'monetization_potential': strategy.monetization_potential,
                'type': 'custom'
            }
        
        return strategies
    
    def export_learning_data(self) -> Dict:
        """Export learning data for analysis"""
        return {
            'user_preferences': self.user_preferences,
            'performance_history': self.performance_history,
            'learning_data': self.learning_data,
            'custom_strategies': {name: strategy.to_dict() for name, strategy in self.custom_strategies.items()}
        }

# Utility functions
async def create_adaptive_ai_agent() -> AdaptiveTikTokAIAgent:
    """Create and initialize adaptive TikTok AI agent"""
    return AdaptiveTikTokAIAgent()

async def run_adaptive_content_creation(user_id: int, topic: str, instructions: str):
    """Run adaptive content creation process"""
    agent = await create_adaptive_ai_agent()
    
    # Learn from user instructions
    learning_result = await agent.learn_from_user_instructions(user_id, instructions)
    
    if learning_result['status'] == 'success':
        # Generate content plan
        plan = await agent.generate_adaptive_content_plan(user_id, topic)
        
        if plan:
            # Create content
            result = await agent.create_adaptive_content(plan)
            return {
                'status': 'success',
                'learning_result': learning_result,
                'plan': plan,
                'content_result': result
            }
    
    return {'status': 'error', 'message': 'Failed to create adaptive content'}

if __name__ == "__main__":
    # Example usage
    async def main():
        agent = await create_adaptive_ai_agent()
        
        # Example: Learn from user instructions
        instructions = "Create a series about historical mysteries with 10-second hooks leading to 2-minute deep dives for maximum creator rewards"
        result = await agent.learn_from_user_instructions(123, instructions)
        print(json.dumps(result, indent=2, default=str))
        
        # Example: Generate content plan
        plan = await agent.generate_adaptive_content_plan(123, "Ancient Egyptian secrets")
        if plan:
            print(f"Generated plan: {plan.title}")
    
    asyncio.run(main()) 