import os
import json
import asyncio
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from loguru import logger
import sqlite3
from pathlib import Path

# Import existing MediaBot functions
from txt2img import generate_image_from_text
from media_utils import process_image_to_video
from long_video import LongVideoGenerator
from config import COMFYUI_URL, COMFYUI_OUTPUT_DIR, WORKFLOW_FILE, GENERATION_TIMEOUT
from server_utils import restart_comfyui, wait_for_comfyui_ready

# Cerebras API Configuration
CEREBRAS_API_URL = os.getenv('CEREBRAS_API_URL', 'https://api.cerebras.ai/v1')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')

# Global state to track last workflow used (similar to bot.py)
LAST_WORKFLOW = None  # 'txt2img' or 'video'

@dataclass
class ContentStrategy:
    """Content strategy created entirely from user input"""
    project_id: str
    name: str
    description: str
    user_instructions: str
    content_type: str
    duration_range: Dict[str, int]  # min, max, optimal
    target_audience: str
    viral_formula: str
    psychological_triggers: List[str]
    hashtags: List[str]
    monetization_strategy: Dict[str, Any]
    prompt_templates: List[str]
    created_at: str
    updated_at: str
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ContentPlan:
    """Content plan generated from strategy"""
    project_id: str
    strategy_name: str
    title: str
    description: str
    topic: str
    duration: int
    segments: List[Dict]
    hashtags: List[str]
    expected_performance: Dict[str, Any]
    prompt: str
    created_at: str

class SimpleAIAgent:
    """Simple AI Agent that learns strategies entirely from user input"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.cerebras_client = self._init_cerebras_client()
        self.db_path = Path("ai_agent_data.db")
        self._init_database()
    
    async def ensure_comfyui_ready_for_video(self):
        """Ensure ComfyUI is ready for video generation by restarting if needed"""
        global LAST_WORKFLOW
        
        if LAST_WORKFLOW == 'txt2img':
            logger.info("AI Agent: Switching from text-to-image to video workflow - restarting ComfyUI")
            
            if restart_comfyui():
                logger.info("AI Agent: ComfyUI restarted successfully for video workflow")
                
                # Wait for ComfyUI to be ready
                if await wait_for_comfyui_ready(COMFYUI_URL):
                    logger.info("AI Agent: ComfyUI is ready for video workflow")
                    LAST_WORKFLOW = 'video'
                    return True
                else:
                    logger.error("AI Agent: ComfyUI did not become ready after restart")
                    return False
            else:
                logger.error("AI Agent: Failed to restart ComfyUI for video workflow")
                return False
        
        # If last workflow was video or None, no restart needed
        LAST_WORKFLOW = 'video'
        return True
    
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
    
    def _init_database(self):
        """Initialize SQLite database for storing strategies and plans"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create strategies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategies (
                project_id TEXT,
                name TEXT,
                description TEXT,
                user_instructions TEXT,
                content_type TEXT,
                duration_range TEXT,
                target_audience TEXT,
                viral_formula TEXT,
                psychological_triggers TEXT,
                hashtags TEXT,
                monetization_strategy TEXT,
                prompt_templates TEXT,
                created_at TEXT,
                updated_at TEXT,
                PRIMARY KEY (project_id, name)
            )
        ''')
        
        # Create content_plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_plans (
                project_id TEXT,
                strategy_name TEXT,
                title TEXT,
                description TEXT,
                topic TEXT,
                duration INTEGER,
                segments TEXT,
                hashtags TEXT,
                expected_performance TEXT,
                prompt TEXT,
                created_at TEXT
            )
        ''')
        
        # Create performance_data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_data (
                project_id TEXT,
                strategy_name TEXT,
                content_title TEXT,
                metrics TEXT,
                analysis TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def learn_strategy(self, user_instructions: str, strategy_name: str) -> Dict:
        """Learn and create a new strategy entirely from user instructions"""
        try:
            # Analyze user instructions using Cerebras API
            analysis_prompt = f"""
            Analyze these user instructions for TikTok content creation and extract structured data.
            
            User Instructions: "{user_instructions}"
            
            Extract and return ONLY a JSON object with this exact structure:
            {{
                "description": "Brief description of the content strategy",
                "content_type": "single/series/ladder/documentary",
                "duration_range": {{
                    "min": 10,
                    "max": 300,
                    "optimal": 90
                }},
                "target_audience": "Description of target audience",
                "viral_formula": "hook_to_payoff/progressive_learning/investigative_revelation/transformation_reveal",
                "psychological_triggers": ["curiosity", "surprise", "satisfaction"],
                "hashtags": ["#relevant", "#hashtags"],
                "monetization_strategy": {{
                    "primary": "creator_rewards/tiktok_shop/brand_sponsorships",
                    "secondary": "affiliate_marketing/course_sales",
                    "target_revenue_per_1k_views": 0.80
                }},
                "prompt_templates": [
                    "Template 1 for content generation",
                    "Template 2 for content generation"
                ]
            }}
            
            Focus on extracting the user's specific requirements and preferences.
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
                    
                    # Create strategy object
                    strategy = ContentStrategy(
                        project_id=self.project_id,
                        name=strategy_name,
                        description=analysis['description'],
                        user_instructions=user_instructions,
                        content_type=analysis['content_type'],
                        duration_range=analysis['duration_range'],
                        target_audience=analysis['target_audience'],
                        viral_formula=analysis['viral_formula'],
                        psychological_triggers=analysis['psychological_triggers'],
                        hashtags=analysis['hashtags'],
                        monetization_strategy=analysis['monetization_strategy'],
                        prompt_templates=analysis['prompt_templates'],
                        created_at=datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat()
                    )
                    
                    # Save to database
                    self._save_strategy(strategy)
                    
                    return {
                        'status': 'success',
                        'strategy': strategy.to_dict(),
                        'message': f"Strategy '{strategy_name}' learned successfully"
                    }
            
            return {'status': 'error', 'message': 'Failed to analyze instructions'}
            
        except Exception as e:
            logger.error(f"Error learning strategy: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _save_strategy(self, strategy: ContentStrategy):
        """Save strategy to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO strategies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            strategy.project_id,
            strategy.name,
            strategy.description,
            strategy.user_instructions,
            strategy.content_type,
            json.dumps(strategy.duration_range),
            strategy.target_audience,
            strategy.viral_formula,
            json.dumps(strategy.psychological_triggers),
            json.dumps(strategy.hashtags),
            json.dumps(strategy.monetization_strategy),
            json.dumps(strategy.prompt_templates),
            strategy.created_at,
            strategy.updated_at
        ))
        
        conn.commit()
        conn.close()
    
    def get_strategies(self) -> List[Dict]:
        """Get all strategies for this project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM strategies WHERE project_id = ?
        ''', (self.project_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        strategies = []
        for row in rows:
            strategy = {
                'project_id': row[0],
                'name': row[1],
                'description': row[2],
                'user_instructions': row[3],
                'content_type': row[4],
                'duration_range': json.loads(row[5]),
                'target_audience': row[6],
                'viral_formula': row[7],
                'psychological_triggers': json.loads(row[8]),
                'hashtags': json.loads(row[9]),
                'monetization_strategy': json.loads(row[10]),
                'prompt_templates': json.loads(row[11]),
                'created_at': row[12],
                'updated_at': row[13]
            }
            strategies.append(strategy)
        
        return strategies
    
    def get_strategy(self, strategy_name: str) -> Optional[Dict]:
        """Get specific strategy by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM strategies WHERE project_id = ? AND name = ?
        ''', (self.project_id, strategy_name))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'project_id': row[0],
                'name': row[1],
                'description': row[2],
                'user_instructions': row[3],
                'content_type': row[4],
                'duration_range': json.loads(row[5]),
                'target_audience': row[6],
                'viral_formula': row[7],
                'psychological_triggers': json.loads(row[8]),
                'hashtags': json.loads(row[9]),
                'monetization_strategy': json.loads(row[10]),
                'prompt_templates': json.loads(row[11]),
                'created_at': row[12],
                'updated_at': row[13]
            }
        
        return None
    
    async def generate_content_plan(self, topic: str, strategy_name: str) -> Optional[ContentPlan]:
        """Generate content plan using learned strategy"""
        try:
            # Get strategy from database
            strategy_data = self.get_strategy(strategy_name)
            if not strategy_data:
                logger.error(f"Strategy '{strategy_name}' not found")
                return None
            
            # Generate content plan using Cerebras API
            plan_prompt = f"""
            Create a TikTok content plan using this strategy:
            
            Strategy: {strategy_data['name']}
            Description: {strategy_data['description']}
            User Instructions: {strategy_data['user_instructions']}
            Content Type: {strategy_data['content_type']}
            Duration Range: {strategy_data['duration_range']['min']}-{strategy_data['duration_range']['max']} seconds
            Target Audience: {strategy_data['target_audience']}
            Viral Formula: {strategy_data['viral_formula']}
            Psychological Triggers: {', '.join(strategy_data['psychological_triggers'])}
            Hashtags: {', '.join(strategy_data['hashtags'])}
            
            Topic: "{topic}"
            
            Generate ONLY a JSON response with this structure:
            {{
                "title": "Engaging title for the video",
                "description": "Brief description of the content",
                "duration": {strategy_data['duration_range']['optimal']},
                "segments": [
                    {{
                        "prompt": "Detailed prompt for AI generation",
                        "frames": 50,
                        "duration": 15,
                        "purpose": "hook/content/conclusion"
                    }}
                ],
                "hashtags": ["#relevant", "#hashtags"],
                "expected_performance": {{
                    "views": 50000,
                    "likes": 2500,
                    "shares": 500,
                    "comments": 200
                }},
                "prompt": "Main prompt for content generation"
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
                    
                    plan = ContentPlan(
                        project_id=self.project_id,
                        strategy_name=strategy_name,
                        title=plan_data['title'],
                        description=plan_data['description'],
                        topic=topic,
                        duration=plan_data['duration'],
                        segments=plan_data['segments'],
                        hashtags=plan_data['hashtags'],
                        expected_performance=plan_data['expected_performance'],
                        prompt=plan_data['prompt'],
                        created_at=datetime.now().isoformat()
                    )
                    
                    # Save plan to database
                    self._save_content_plan(plan)
                    
                    return plan
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating content plan: {e}")
            return None
    
    def _save_content_plan(self, plan: ContentPlan):
        """Save content plan to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO content_plans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            plan.project_id,
            plan.strategy_name,
            plan.title,
            plan.description,
            plan.topic,
            plan.duration,
            json.dumps(plan.segments),
            json.dumps(plan.hashtags),
            json.dumps(plan.expected_performance),
            plan.prompt,
            plan.created_at
        ))
        
        conn.commit()
        conn.close()
    
    async def create_content(self, plan: ContentPlan) -> Optional[str]:
        """Create content using the plan"""
        global LAST_WORKFLOW
        
        try:
            logger.info(f"Creating content: {plan.title}")
            
            # Generate initial image (set workflow to txt2img)
            logger.info("Generating initial image...")
            LAST_WORKFLOW = 'txt2img'
            image_path = await generate_image_from_text(plan.prompt, COMFYUI_URL, COMFYUI_OUTPUT_DIR)
            
            if not image_path or not os.path.exists(image_path):
                logger.error("Failed to generate initial image")
                return None
            
            # Create video based on content type
            if len(plan.segments) == 1:
                # Single video - ensure ComfyUI is ready for video generation
                if not await self.ensure_comfyui_ready_for_video():
                    logger.error("Failed to prepare ComfyUI for video generation")
                    return None
                
                segment = plan.segments[0]
                await process_image_to_video(
                    segment['prompt'], 
                    image_path, 
                    segment['frames'], 
                    COMFYUI_URL, 
                    WORKFLOW_FILE
                )
            else:
                # Multi-segment video - ensure ComfyUI is ready for video generation
                if not await self.ensure_comfyui_ready_for_video():
                    logger.error("Failed to prepare ComfyUI for video generation")
                    return None
                
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
            
            logger.info("Content creation completed")
            return "content_created"
            
        except Exception as e:
            logger.error(f"Error creating content: {e}")
            return None
    
    async def update_performance(self, strategy_name: str, content_title: str, metrics: Dict):
        """Update performance data for strategy learning"""
        try:
            # Analyze performance using Cerebras API
            analysis_prompt = f"""
            Analyze this content performance and provide improvement suggestions:
            
            Strategy: {strategy_name}
            Content: {content_title}
            Performance: {json.dumps(metrics, indent=2)}
            
            Provide ONLY a JSON response with this structure:
            {{
                "performance_score": 0.85,
                "strengths": ["list", "of", "strengths"],
                "weaknesses": ["list", "of", "weaknesses"],
                "improvements": ["list", "of", "suggestions"],
                "strategy_adjustments": {{
                    "duration": "adjustment",
                    "formula": "adjustment"
                }}
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
                    
                    # Save performance data
                    self._save_performance_data(strategy_name, content_title, metrics, analysis)
                    
                    return analysis
            
            return {}
            
        except Exception as e:
            logger.error(f"Error updating performance: {e}")
            return {}
    
    def _save_performance_data(self, strategy_name: str, content_title: str, metrics: Dict, analysis: Dict):
        """Save performance data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO performance_data VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.project_id,
            strategy_name,
            content_title,
            json.dumps(metrics),
            json.dumps(analysis),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_performance_history(self, strategy_name: Optional[str] = None) -> List[Dict]:
        """Get performance history for this project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if strategy_name:
            cursor.execute('''
                SELECT * FROM performance_data WHERE project_id = ? AND strategy_name = ?
                ORDER BY created_at DESC
            ''', (self.project_id, strategy_name))
        else:
            cursor.execute('''
                SELECT * FROM performance_data WHERE project_id = ?
                ORDER BY created_at DESC
            ''', (self.project_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'project_id': row[0],
                'strategy_name': row[1],
                'content_title': row[2],
                'metrics': json.loads(row[3]),
                'analysis': json.loads(row[4]),
                'created_at': row[5]
            })
        
        return history
    
    def export_project_data(self) -> Dict:
        """Export all project data"""
        return {
            'project_id': self.project_id,
            'strategies': self.get_strategies(),
            'performance_history': self.get_performance_history()
        }

# Utility functions
async def create_simple_ai_agent(project_id: str) -> SimpleAIAgent:
    """Create simple AI agent for specific project"""
    return SimpleAIAgent(project_id)

async def run_simple_content_creation(project_id: str, topic: str, strategy_name: str, user_instructions: str):
    """Run simple content creation process"""
    agent = await create_simple_ai_agent(project_id)
    
    # Learn strategy if it doesn't exist
    existing_strategy = agent.get_strategy(strategy_name)
    if not existing_strategy:
        learning_result = await agent.learn_strategy(user_instructions, strategy_name)
        if learning_result['status'] != 'success':
            return learning_result
    
    # Generate content plan
    plan = await agent.generate_content_plan(topic, strategy_name)
    
    if plan:
        # Create content
        result = await agent.create_content(plan)
        return {
            'status': 'success',
            'plan': plan.__dict__,
            'content_result': result
        }
    
    return {'status': 'error', 'message': 'Failed to create content'}

if __name__ == "__main__":
    # Example usage
    async def main():
        project_id = "test_project_123"
        agent = await create_simple_ai_agent(project_id)
        
        # Example: Learn strategy
        instructions = "Create 10-second hooks leading to 2-minute deep dives for maximum creator rewards"
        result = await agent.learn_strategy(instructions, "hook_to_payoff")
        print(json.dumps(result, indent=2, default=str))
        
        # Example: Generate content plan
        plan = await agent.generate_content_plan("Ancient Egyptian secrets", "hook_to_payoff")
        if plan:
            print(f"Generated plan: {plan.title}")
    
    asyncio.run(main()) 