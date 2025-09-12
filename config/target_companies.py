"""
Configuration for target companies and employee criteria
"""

# Major tech companies to track
TARGET_COMPANIES = [
    'openai',
    'cohere', 
    'mistral',
    'meta',
    'google deepmind',  # Correct company name as per LinkedIn
    'anthropic',
    'uber',
    'airbnb',
    'scale ai',
    'linkedin',
    'palantir',
    'microsoft',
    'google'
]

# Senior roles to track
SENIOR_ROLES = [
    'engineering',
    'research', 
    'product',
    'design',
    'data science',
    'machine learning',
    'artificial intelligence'
]

SENIOR_LEVELS = [
    'senior',
    'lead',
    'principal', 
    'staff',
    'director',
    'vp',
    'head',
    'chief'
]

# AI/ML related keywords for filtering
AI_ML_KEYWORDS = [
    'machine learning',
    'artificial intelligence',
    'deep learning',
    'neural network',
    'nlp',
    'natural language',
    'computer vision',
    'reinforcement learning',
    'generative ai',
    'llm',
    'large language model',
    'transformer',
    'gpt',
    'diffusion',
    'ai research',
    'ml engineer',
    'ai engineer',
    'data scientist',
    'research scientist',
    'research engineer',
    'ai product',
    'ml platform',
    'ai infrastructure'
]

# Technical role keywords - roles we WANT to track
TECHNICAL_ROLE_KEYWORDS = [
    # Engineering Roles
    'engineer',
    'developer',
    'programmer',
    'architect',
    'devops',
    'sre',  # Site Reliability Engineer
    'infrastructure',
    'backend',
    'frontend',
    'full stack',
    'fullstack',
    'software',
    'platform',
    'systems',
    'network',
    
    # AI/ML/Data Roles
    'machine learning',
    'ml engineer',
    'ai engineer',
    'artificial intelligence',
    'data scientist',
    'data engineer',
    'research scientist',
    'research engineer',
    'applied scientist',
    'deep learning',
    'computer vision',
    'nlp',
    'robotics',
    
    # Product & Technical Leadership
    'product manager',
    'product owner',
    'technical product',
    'cto',
    'chief technology',
    'engineering manager',
    'engineering director',
    'vp engineering',
    'head of engineering',
    'tech lead',
    'technical lead',
    'principal',
    'staff',
    'architect',
    
    # Research & Science
    'researcher',
    'research',
    'scientist'
]

# Non-technical keywords - roles we DON'T want
NON_TECHNICAL_KEYWORDS = [
    # Sales & Business
    'sales',
    'gtm',  # Go-to-market roles
    'go-to-market',
    'account executive',
    'account manager',
    'account director',
    'business development',
    'partnerships',
    'enterprise',
    'customer success',
    'client solutions',
    
    # Marketing & Communications
    'marketing',
    'communications',
    'pr manager',
    'public relations',
    'content',
    'brand',
    'growth marketing',
    'community manager',
    'social media',
    
    # Operations & Support
    'operations',
    'hr',
    'human resources',
    'recruiter',
    'recruiting',
    'talent',
    'finance',
    'accounting',
    'legal',
    'compliance',
    'administrative',
    'office manager',
    
    # Non-Technical Management
    'chief of staff',
    'program manager',  # Often non-technical
    'project manager',  # Often non-technical
    'delivery manager',
    
    # Other Non-Technical
    'designer',  # Unless specifically 'product designer'
    'ux designer',  # Unless working on technical tools
    'graphic',
    'creative director',
    'art director'
]

# Skills that indicate AI/ML expertise
AI_ML_SKILLS = [
    'pytorch',
    'tensorflow',
    'jax',
    'scikit-learn',
    'keras',
    'cuda',
    'transformers',
    'hugging face',
    'langchain',
    'vector database',
    'embeddings',
    'fine-tuning',
    'model training',
    'model deployment',
    'mlops',
    'deep learning',
    'computer vision',
    'natural language processing'
]