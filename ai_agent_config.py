import os
from typing import Dict, List
from dataclasses import dataclass

# AI Agent Configuration
@dataclass
class AIConfig:
    """Configuration for AI Agent"""
    # Cerebras API Settings
    cerebras_api_url: str = os.getenv('CEREBRAS_API_URL', 'https://api.cerebras.ai/v1')
    cerebras_api_key: str = os.getenv('CEREBRAS_API_KEY', '')
    cerebras_model: str = os.getenv('CEREBRAS_MODEL', 'cerebras-llama-3.1-8b-instruct')
    
    # Content Generation Settings
    max_daily_content: int = int(os.getenv('MAX_DAILY_CONTENT', '5'))
    content_creation_timeout: int = int(os.getenv('CONTENT_CREATION_TIMEOUT', '3600'))
    max_retries: int = int(os.getenv('MAX_RETRIES', '3'))
    
    # Performance Settings
    min_expected_views: int = int(os.getenv('MIN_EXPECTED_VIEWS', '10000'))
    target_engagement_rate: float = float(os.getenv('TARGET_ENGAGEMENT_RATE', '0.05'))
    
    # Posting Schedule (24-hour format)
    optimal_posting_hours: List[int] = [14, 15, 16, 17, 18]  # 2-6 PM EST
    posting_days: List[int] = [0, 1, 2, 3, 4]  # Monday-Friday
    
    # Content Quality Settings
    min_video_duration: int = 10  # seconds
    max_video_duration: int = 60  # seconds
    target_aspect_ratio: str = "9:16"  # TikTok vertical format
    
    # Hashtag Strategy
    max_hashtags_per_video: int = 5
    trending_hashtag_weight: float = 0.7
    niche_hashtag_weight: float = 0.3

# Content Strategy Templates
CONTENT_STRATEGIES = {
    'invisible_expertise': {
        'niche': 'invisible_expertise',
        'target_audience': 'DIY enthusiasts, professionals, home improvement',
        'content_type': 'educational',
        'viral_formula': 'hook_body_conclusion',
        'psychological_triggers': ['curiosity', 'expertise', 'satisfaction', 'surprise'],
        'optimal_duration': 21,
        'hashtags': ['#DIY', '#HowTo', '#LifeHacks', '#ExpertTips', '#HomeImprovement'],
        'monetization_potential': 0.80,
        'prompt_templates': [
            "Professional close-up macro shot of {process} with perfect lighting, smooth camera movement revealing step-by-step transformation, clean minimalist background, documentary-style realism",
            "Split-screen comparison showing dramatic before/after of {subject}, soft natural lighting, slow zoom revealing key differences, satisfying visual progression"
        ]
    },
    
    'historical_humor': {
        'niche': 'historical_humor',
        'target_audience': 'history buffs, comedy lovers, educational content consumers',
        'content_type': 'entertainment',
        'viral_formula': 'transformation_reveal',
        'psychological_triggers': ['surprise', 'humor', 'novelty', 'curiosity'],
        'optimal_duration': 34,
        'hashtags': ['#History', '#Funny', '#HistoricalFacts', '#Comedy', '#Educational'],
        'monetization_potential': 0.60,
        'prompt_templates': [
            "Cinematic reimagining of {historical_event} with modern twist, dramatic lighting, period-accurate costumes with contemporary elements, engaging visual storytelling",
            "Before/after transformation showing {historical_figure} in modern context, seamless transition effects, humorous visual elements"
        ]
    },
    
    'marine_education': {
        'niche': 'marine_education',
        'target_audience': 'nature lovers, science enthusiasts, ocean conservationists',
        'content_type': 'educational',
        'viral_formula': 'mystery_hook',
        'psychological_triggers': ['awe', 'curiosity', 'fear', 'wonder'],
        'optimal_duration': 28,
        'hashtags': ['#Ocean', '#MarineLife', '#Science', '#Nature', '#OceanConservation'],
        'monetization_potential': 0.90,
        'prompt_templates': [
            "Mysterious underwater scene with {marine_creature}, atmospheric blue lighting creating intrigue, camera slowly reveals surprising context, building suspense",
            "Dramatic ocean disaster visualization, powerful waves and weather effects, documentary-style cinematography, awe-inspiring natural forces"
        ]
    },
    
    'geographic_micro_niche': {
        'niche': 'geographic_micro_niche',
        'target_audience': 'cultural enthusiasts, travelers, heritage lovers',
        'content_type': 'educational',
        'viral_formula': 'hook_body_conclusion',
        'psychological_triggers': ['belonging', 'curiosity', 'pride', 'nostalgia'],
        'optimal_duration': 25,
        'hashtags': ['#Culture', '#Travel', '#Heritage', '#Community', '#Traditions'],
        'monetization_potential': 0.70,
        'prompt_templates': [
            "Beautiful cultural celebration scene from {region}, vibrant traditional costumes, authentic atmosphere, community gathering, warm natural lighting",
            "Traditional craftsmanship process from {culture}, close-up macro shots of intricate details, skilled hands at work, cultural significance highlighted"
        ]
    }
}

# Viral Content Formulas
VIRAL_FORMULAS = {
    'hook_body_conclusion': {
        'structure': [
            {'type': 'hook', 'duration': 3, 'purpose': 'Grab attention immediately'},
            {'type': 'body', 'duration': 15, 'purpose': 'Deliver main content'},
            {'type': 'conclusion', 'duration': 3, 'purpose': 'Call to action or surprise ending'}
        ],
        'psychological_triggers': ['curiosity', 'surprise', 'satisfaction']
    },
    
    'transformation_reveal': {
        'structure': [
            {'type': 'setup', 'duration': 5, 'purpose': 'Establish context'},
            {'type': 'transformation', 'duration': 15, 'purpose': 'Show dramatic change'},
            {'type': 'reveal', 'duration': 5, 'purpose': 'Final reveal or twist'}
        ],
        'psychological_triggers': ['anticipation', 'surprise', 'satisfaction']
    },
    
    'mystery_hook': {
        'structure': [
            {'type': 'mystery', 'duration': 8, 'purpose': 'Create intrigue'},
            {'type': 'development', 'duration': 12, 'purpose': 'Build suspense'},
            {'type': 'resolution', 'duration': 5, 'purpose': 'Reveal the answer'}
        ],
        'psychological_triggers': ['curiosity', 'suspense', 'relief']
    }
}

# Trending Topic Categories
TRENDING_CATEGORIES = {
    'technology': ['AI', 'gadgets', 'software', 'automation', 'innovation'],
    'lifestyle': ['fitness', 'cooking', 'fashion', 'beauty', 'wellness'],
    'education': ['science', 'history', 'language', 'skills', 'facts'],
    'entertainment': ['movies', 'music', 'gaming', 'comedy', 'dance'],
    'current_events': ['news', 'politics', 'sports', 'celebrity', 'viral']
}

# Performance Metrics
PERFORMANCE_METRICS = {
    'views': {'weight': 0.3, 'target': 50000},
    'likes': {'weight': 0.2, 'target': 2500},
    'shares': {'weight': 0.25, 'target': 500},
    'comments': {'weight': 0.15, 'target': 200},
    'saves': {'weight': 0.1, 'target': 100}
}

# Content Quality Filters
QUALITY_FILTERS = {
    'min_resolution': (1080, 1920),
    'max_file_size_mb': 50,
    'required_aspect_ratio': '9:16',
    'min_duration_seconds': 10,
    'max_duration_seconds': 60,
    'forbidden_content': [
        'violence', 'nudity', 'hate_speech', 'misinformation',
        'copyright_violation', 'spam', 'low_quality'
    ]
}

# AI Prompt Optimization
PROMPT_OPTIMIZATION = {
    'required_elements': [
        'specific visual descriptors',
        'professional lighting',
        'camera movement',
        'color grading',
        'mobile optimization'
    ],
    'avoided_elements': [
        'uncanny valley effects',
        'human faces (when possible)',
        'obvious AI artifacts',
        'low resolution',
        'poor composition'
    ],
    'enhancement_keywords': [
        'professional camera shot',
        'commercial photography style',
        'natural movement',
        'realistic physics',
        'cinematic quality',
        'documentary realism'
    ]
}

# Default configuration instance
ai_config = AIConfig() 