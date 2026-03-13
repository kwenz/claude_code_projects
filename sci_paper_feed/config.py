"""Configuration settings for the research paper feed app."""

import os
from dotenv import load_dotenv

load_dotenv()

# LLM Provider Configuration
# Options: 'openai', 'huggingface', 'gemini', 'local'
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'huggingface')

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')  # Free at https://huggingface.co/settings/tokens
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Free at https://aistudio.google.com/

# arXiv configuration
ARXIV_API_URL = "http://export.arxiv.org/api/query"
# ARXIV_CATEGORY = "hep-th"  # Physics category
ARXIV_CATEGORY = "cs.AI"  # AI category

# App settings
MAX_PAPERS_TO_ANALYZE = 50   # Max papers to analyze per day
MAX_PAPERS_LOOKBACK = 200    # Max total papers to analyze in a single refresh (across all days)
TOP_PAPERS_COUNT = 5         # Number of top papers to display
ANALYSIS_BATCH_SIZE = 10     # Number of papers to analyze in each batch

# Database settings
DATABASE_PATH = os.getenv('DATABASE_PATH', 'papers.db')

# Web app settings
AVAILABLE_FIELDS = ['cs.AI', 'hep-th', 'cs.HC']  # Supported arXiv fields
DAYS_TO_DISPLAY = 7  # Number of days to show on the web interface

# Server settings
SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
SERVER_PORT = int(os.getenv('SERVER_PORT', '8501'))

# Model configurations for different providers
MODEL_CONFIGS = {
    'openai': {
        'model': 'gpt-4o-mini',
        'max_tokens': 4000,
        'temperature': 0.05
    },
    'huggingface': {
        'model': 'microsoft/DialoGPT-large',  # Free model
        'max_tokens': 2000,
        'temperature': 0.05
    },
    'gemini': {
        'model': 'gemini-2.5-flash',  # Free tier available
        'max_tokens': 4000,
        'temperature': 0.05,
        'min_request_interval': 13,  # seconds; free tier = 5 req/min
    }
}
