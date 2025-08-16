import os
import json
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import random

# Import existing MediaBot functions
from txt2img import generate_image_from_text
from media_utils import process_image_to_video
from long_video import LongVideoGenerator
from config import COMFYUI_URL, COMFYUI_OUTPUT_DIR, WORKFLOW_FILE, GENERATION_TIMEOUT

# Cerebras API Configuration
CEREBRAS_API_URL = os.getenv('CEREBRAS_API_URL', 'https://api.cerebras.ai/v1')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')

@dataclass
class ContentStrategy:
    """Content strategy configuration for TikTok videos"""
    niche: str
    target_audience: str
    content_type: str  # 'educational', 'entertainment', 'transformative', 'mystery'
    viral_formula: str  # 'hook_body_conclusion', 'transformation_reveal', 'mystery_hook'
    psychological_triggers: List[str]
    optimal_duration: int  # seconds
    hashtags: List[str]
    monetization_potential: float  # $ per 1000 views

@dataclass
class ContentPlan:
    """Individual content piece plan"""
    title: str
    description: str
    prompt: str
    target_duration: int
    segments: List[Dict]
    hashtags: List[str]
    posting_time: datetime
    expected_performance: Dict

class TikTokAIAgent:
    """AI Agent for automated TikTok content creation using Cerebras API"""
    
    def __init__(self):
        self.cerebras_client = self._init_cerebras_client()
        self.content_strategies = self._load_content_strategies()
        self.trending_topics = []
        self.performance_history = []
        
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
    
    def _load_content_strategies(self) -> Dict[str, ContentStrategy]:
        """Load predefined content strategies based on TikTok strategy document"""
        return {
            'invisible_expertise': ContentStrategy(
                niche='invisible_expertise',
                target_audience='DIY enthusiasts, professionals',
                content_type='educational',
                viral_formula='hook_body_conclusion',
                psychological_triggers=['curiosity', 'expertise', 'satisfaction'],
                optimal_duration=21,
                hashtags=['#DIY', '#HowTo', '#LifeHacks', '#ExpertTips'],
                monetization_potential=0.80
            ),
            'historical_humor': ContentStrategy(
                niche='historical_humor',
                target_audience='history buffs, comedy lovers',
                content_type='entertainment',
                viral_formula='transformation_reveal',
                psychological_triggers=['surprise', 'humor', 'novelty'],
                optimal_duration=34,
                hashtags=['#History', '#Funny', '#HistoricalFacts', '#Comedy'],
                monetization_potential=0.60
            ),
            'marine_education': ContentStrategy(
                niche='marine_education',
                target_audience='nature lovers, science enthusiasts',
                content_type='educational',
                viral_formula='mystery_hook',
                psychological_triggers=['awe', 'curiosity', 'fear'],
                optimal_duration=28,
                hashtags=['#Ocean', '#MarineLife', '#Science', '#Nature'],
                monetization_potential=0.90
            ),
            'geographic_micro_niche': ContentStrategy(
                niche='geographic_micro_niche',
                target_audience='cultural enthusiasts, travelers',
                content_type='educational',
                viral_formula='hook_body_conclusion',
                psychological_triggers=['belonging', 'curiosity', 'pride'],
                optimal_duration=25,
                hashtags=['#Culture', '#Travel', '#Heritage', '#Community'],
                monetization_potential=0.70
            )
        }
    
    async def analyze_trending_topics(self) -> List[str]:
        """Analyze current trending topics using Cerebras API"""
        try:
            prompt = """
            Analyze current TikTok trends and identify 10 trending topics that would work well for AI-generated content.
            Focus on topics that:
            1. Have high engagement potential
            2. Can be visualized effectively with AI
            3. Haven't been oversaturated with AI content
            4. Align with educational or entertainment value
            
            Return only the topic names, one per line.
            """
            
            response = requests.post(
                f"{self.cerebras_client['base_url']}/chat/completions",
                headers=self.cerebras_client['headers'],
                json={
                    "model": "cerebras-llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                topics = response.json()['choices'][0]['message']['content'].strip().split('\n')
                self.trending_topics = [topic.strip() for topic in topics if topic.strip()]
                logger.info(f"Analyzed {len(self.trending_topics)} trending topics")
                return self.trending_topics
            else:
                logger.error(f"Failed to analyze trending topics: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error analyzing trending topics: {e}")
            return []
    
    async def generate_content_plan(self, strategy: ContentStrategy, topic: str) -> ContentPlan:
        """Generate a complete content plan using Cerebras API"""
        try:
            prompt = f"""
            Create a TikTok content plan for topic: "{topic}"
            
            Strategy details:
            - Niche: {strategy.niche}
            - Target audience: {strategy.target_audience}
            - Content type: {strategy.content_type}
            - Viral formula: {strategy.viral_formula}
            - Psychological triggers: {', '.join(strategy.psychological_triggers)}
            - Target duration: {strategy.optimal_duration} seconds
            
            Generate a JSON response with the following structure:
            {{
                "title": "Engaging title for the video",
                "description": "Brief description of the content",
                "prompt": "Detailed prompt for AI image/video generation",
                "target_duration": {strategy.optimal_duration},
                "segments": [
                    {{
                        "prompt": "Segment 1 prompt",
                        "frames": 50,
                        "duration": 10
                    }},
                    {{
                        "prompt": "Segment 2 prompt", 
                        "frames": 50,
                        "duration": 10
                    }}
                ],
                "hashtags": ["#relevant", "#hashtags"],
                "expected_performance": {{
                    "views": 50000,
                    "likes": 2500,
                    "shares": 500,
                    "comments": 200
                }}
            }}
            
            Make sure the content is engaging, educational, and optimized for TikTok's algorithm.
            """
            
            response = requests.post(
                f"{self.cerebras_client['base_url']}/chat/completions",
                headers=self.cerebras_client['headers'],
                json={
                    "model": "cerebras-llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.8
                }
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    plan_data = json.loads(content[json_start:json_end])
                    
                    return ContentPlan(
                        title=plan_data['title'],
                        description=plan_data['description'],
                        prompt=plan_data['prompt'],
                        target_duration=plan_data['target_duration'],
                        segments=plan_data['segments'],
                        hashtags=plan_data['hashtags'],
                        posting_time=datetime.now() + timedelta(hours=random.randint(2, 24)),
                        expected_performance=plan_data['expected_performance']
                    )
            
            logger.error(f"Failed to generate content plan: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating content plan: {e}")
            return None
    
    async def generate_optimized_prompt(self, base_prompt: str, strategy: ContentStrategy) -> str:
        """Generate an optimized prompt for AI generation using Cerebras API"""
        try:
            prompt = f"""
            Optimize this prompt for AI video generation using WAN 2.1/2.2:
            
            Original prompt: "{base_prompt}"
            
            Strategy: {strategy.niche}
            Target duration: {strategy.optimal_duration} seconds
            Psychological triggers: {', '.join(strategy.psychological_triggers)}
            
            Apply these optimization techniques:
            1. Use specific visual descriptors (close-up, macro shot, etc.)
            2. Include professional lighting and camera movement
            3. Add cinematic color grading
            4. Ensure mobile-optimized viewing (1080x1920)
            5. Include natural movement and realistic physics
            6. Avoid uncanny valley effects
            7. Focus on objects, landscapes, or abstract concepts
            
            Return only the optimized prompt.
            """
            
            response = requests.post(
                f"{self.cerebras_client['base_url']}/chat/completions",
                headers=self.cerebras_client['headers'],
                json={
                    "model": "cerebras-llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                optimized_prompt = response.json()['choices'][0]['message']['content'].strip()
                logger.info(f"Generated optimized prompt: {optimized_prompt[:100]}...")
                return optimized_prompt
            else:
                logger.error(f"Failed to optimize prompt: {response.status_code}")
                return base_prompt
                
        except Exception as e:
            logger.error(f"Error optimizing prompt: {e}")
            return base_prompt
    
    async def create_content(self, plan: ContentPlan) -> Optional[str]:
        """Create content using MediaBot functions"""
        try:
            logger.info(f"Creating content: {plan.title}")
            
            # Generate initial image
            logger.info("Generating initial image...")
            image_path = await generate_image_from_text(plan.prompt, COMFYUI_URL, COMFYUI_OUTPUT_DIR)
            
            if not image_path or not os.path.exists(image_path):
                logger.error("Failed to generate initial image")
                return None
            
            # Create video from image
            if len(plan.segments) == 1:
                # Single segment video
                logger.info("Creating single segment video...")
                segment = plan.segments[0]
                await process_image_to_video(
                    segment['prompt'], 
                    image_path, 
                    segment['frames'], 
                    COMFYUI_URL, 
                    WORKFLOW_FILE
                )
            else:
                # Multi-segment video
                logger.info("Creating multi-segment video...")
                generator = LongVideoGenerator(COMFYUI_URL, WORKFLOW_FILE, GENERATION_TIMEOUT)
                
                video_path = await generator.generate_long_video(
                    initial_prompt=plan.segments[0]['prompt'],
                    initial_image=image_path,
                    segments_data=plan.segments
                )
                
                if video_path and os.path.exists(video_path):
                    logger.info(f"Multi-segment video created: {video_path}")
                    return video_path
            
            # Clean up
            if os.path.exists(image_path):
                os.remove(image_path)
            
            logger.info("Content creation completed")
            return "content_created"
            
        except Exception as e:
            logger.error(f"Error creating content: {e}")
            return None
    
    async def analyze_performance(self, content_id: str, metrics: Dict) -> Dict:
        """Analyze content performance and update strategy"""
        try:
            prompt = f"""
            Analyze this TikTok content performance and provide optimization recommendations:
            
            Content ID: {content_id}
            Metrics: {json.dumps(metrics, indent=2)}
            
            Provide analysis in JSON format:
            {{
                "performance_score": 0.85,
                "strengths": ["list", "of", "strengths"],
                "weaknesses": ["list", "of", "weaknesses"],
                "recommendations": ["list", "of", "recommendations"],
                "next_content_strategy": "strategy_name"
            }}
            """
            
            response = requests.post(
                f"{self.cerebras_client['base_url']}/chat/completions",
                headers=self.cerebras_client['headers'],
                json={
                    "model": "cerebras-llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
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
                    self.performance_history.append({
                        'content_id': content_id,
                        'metrics': metrics,
                        'analysis': analysis,
                        'timestamp': datetime.now().isoformat()
                    })
                    return analysis
            
            return {}
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return {}
    
    async def generate_daily_content_plan(self) -> List[ContentPlan]:
        """Generate a complete daily content plan"""
        try:
            # Analyze trending topics
            topics = await self.analyze_trending_topics()
            if not topics:
                logger.warning("No trending topics found, using fallback topics")
                topics = [
                    "Amazing DIY life hacks you need to know",
                    "Historical facts that will blow your mind", 
                    "Incredible ocean discoveries",
                    "Cultural traditions from around the world"
                ]
            
            content_plans = []
            
            # Generate content plans for each strategy
            for strategy_name, strategy in self.content_strategies.items():
                for topic in topics[:2]:  # Use top 2 topics per strategy
                    plan = await self.generate_content_plan(strategy, topic)
                    if plan:
                        # Optimize the prompt
                        plan.prompt = await self.generate_optimized_prompt(plan.prompt, strategy)
                        content_plans.append(plan)
                        logger.info(f"Generated plan for {strategy_name}: {plan.title}")
            
            return content_plans
            
        except Exception as e:
            logger.error(f"Error generating daily content plan: {e}")
            return []
    
    async def execute_content_creation_pipeline(self) -> Dict:
        """Execute the complete content creation pipeline"""
        try:
            logger.info("Starting content creation pipeline...")
            
            # Generate daily content plan
            plans = await self.generate_daily_content_plan()
            if not plans:
                return {"status": "error", "message": "No content plans generated"}
            
            results = []
            
            for i, plan in enumerate(plans):
                logger.info(f"Processing plan {i+1}/{len(plans)}: {plan.title}")
                
                # Create content
                content_result = await self.create_content(plan)
                
                if content_result:
                    results.append({
                        "plan": plan,
                        "status": "success",
                        "content_path": content_result
                    })
                else:
                    results.append({
                        "plan": plan,
                        "status": "failed",
                        "error": "Content creation failed"
                    })
            
            # Save results
            self._save_pipeline_results(results)
            
            return {
                "status": "success",
                "total_plans": len(plans),
                "successful": len([r for r in results if r["status"] == "success"]),
                "failed": len([r for r in results if r["status"] == "failed"]),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in content creation pipeline: {e}")
            return {"status": "error", "message": str(e)}
    
    def _save_pipeline_results(self, results: List[Dict]):
        """Save pipeline results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pipeline_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "results": results
                }, f, indent=2, default=str)
            
            logger.info(f"Pipeline results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving pipeline results: {e}")

# Utility functions for external use
async def create_tiktok_content_agent() -> TikTokAIAgent:
    """Create and initialize TikTok AI agent"""
    return TikTokAIAgent()

async def run_daily_content_creation():
    """Run the daily content creation process"""
    agent = await create_tiktok_content_agent()
    return await agent.execute_content_creation_pipeline()

if __name__ == "__main__":
    # Example usage
    async def main():
        agent = await create_tiktok_content_agent()
        result = await agent.execute_content_creation_pipeline()
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main()) 