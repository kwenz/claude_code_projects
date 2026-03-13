"""Simple test script to verify the app works."""

import os
import sys
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.main import ResearchPaperFeed

# Enable debug logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def test_arxiv_api_only():
    """Test just the arXiv API functionality without LLM."""
    from core.arxiv_client import ArxivClient
    import config
    from datetime import datetime, timedelta
    
    print("Testing arXiv API client...")
    client = ArxivClient()
    
    # Test current date
    print(f"\n📅 Testing current date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"📂 Using category: {config.ARXIV_CATEGORY}")
    papers = client.fetch_daily_papers(category=config.ARXIV_CATEGORY)
    print(f"Found {len(papers)} papers for today")
    
    
    # Return some papers for the test
    return len(papers) > 0

def test_full_app():
    """Test the full application."""
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ OPENAI_API_KEY not set. Skipping full app test.")
        return False
        
    print("Testing full application...")
    feed = ResearchPaperFeed()
    feed_data = feed.generate_daily_feed()
    
    print(f"Generated feed with {len(feed_data.get('top_papers', []))} top papers")
    return len(feed_data.get('top_papers', [])) > 0

if __name__ == "__main__":
    print("🧪 Running tests...\n")
    
    # Test arXiv API
    api_works = test_arxiv_api_only()
    print(f"arXiv API test: {'✅ PASS' if api_works else '❌ FAIL'}\n")
    
    # # Test full app
    # app_works = test_full_app()
    # print(f"Full app test: {'✅ PASS' if app_works else '⚠️ SKIPPED (no API key)'}")
    
    print("\n🎉 Testing complete!")
