"""Main application for the AI research paper feed."""

from datetime import datetime
from typing import List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core.arxiv_client import ArxivClient
from core.paper_analyzer import PaperAnalyzer


class ResearchPaperFeed:
    """Main application class for the research paper feed."""
    
    def __init__(self):
        self.arxiv_client = ArxivClient()
        self.analyzer = PaperAnalyzer()
    
    def generate_daily_feed(self) -> Dict:
        """Generate the daily research paper feed."""
        print(f"🔍 Fetching today's {config.ARXIV_CATEGORY} papers from arXiv API...")
        
        # Fetch papers using arXiv API
        papers = self.arxiv_client.fetch_daily_papers(category=config.ARXIV_CATEGORY)
        
        if not papers:
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'actual_date': 'unknown',
                'total_papers': 0,
                'top_papers': [],
                'daily_summary': "No papers found in recent days.",
                'error': "Could not fetch papers from arXiv"
            }
        
        # Determine the actual date of the papers (from announcement date)
        actual_date = 'unknown'
        if papers and papers[0].get('announcement_date'):
            try:
                paper_date = datetime.fromisoformat(papers[0]['announcement_date'].replace('Z', '+00:00'))
                actual_date = paper_date.strftime('%Y-%m-%d')
            except:
                actual_date = 'unknown'
        
        print(f"📄 Found {len(papers)} papers")
        
        # Limit papers to avoid API costs
        if len(papers) > config.MAX_PAPERS_TO_ANALYZE:
            papers = papers[:config.MAX_PAPERS_TO_ANALYZE]
            print(f"⚠️  Limited analysis to first {config.MAX_PAPERS_TO_ANALYZE} papers")
        
        print("🤖 Analyzing papers with AI...")
        
        # Analyze and rank papers
        top_papers, daily_summary = self.analyzer.analyze_and_rank_papers(
            papers, config.TOP_PAPERS_COUNT
        )
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'actual_date': actual_date,
            'total_papers': len(papers),
            'analyzed_papers': len(papers),
            'top_papers': top_papers,
            'daily_summary': daily_summary
        }
    
    def print_feed(self, feed_data: Dict):
        """Print the feed in a nice format."""
        print("\n" + "="*80)
        print(f"🧠 AI RESEARCH PAPER FEED - {feed_data['date']}")
        if feed_data.get('actual_date') and feed_data['actual_date'] != feed_data['date']:
            print(f"📅 Most recent papers available from: {feed_data['actual_date']}")
        print("="*80)
        
        if 'error' in feed_data:
            print(f"❌ Error: {feed_data['error']}")
            return
        
        print(f"📊 Analyzed {feed_data['analyzed_papers']} papers")
        print(f"🏆 Top {len(feed_data['top_papers'])} most interesting papers:\n")
        
        # Print top papers
        for i, paper in enumerate(feed_data['top_papers'], 1):
            print(f"{i}. **{paper['title']}**")
            print(f"   👥 Authors: {paper['authors']}")
            print(f"   ⭐ Score: {paper.get('score', 'N/A')}/10")
            print(f"   💡 Why it's interesting: {paper.get('explanation', 'No explanation available')}")
            print(f"   🔗 URL: {paper['url']}")
            print()
        
        # Print daily summary
        print("="*80)
        print("📝 DAILY SUMMARY")
        print("="*80)
        print(feed_data['daily_summary'])
        print("="*80)


def main():
    """Main function to run the research paper feed."""
    try:
        # Check if the selected LLM provider is configured
        from core.llm_client import LLMClient
        llm_client = LLMClient()
        
        print(f"🤖 Using LLM provider: {config.LLM_PROVIDER}")
        
        if not llm_client.is_configured():
            print(f"❌ Error: {config.LLM_PROVIDER} is not properly configured!")
            print("\n🔧 Configuration options:")
            print("1. Hugging Face (FREE): Set HUGGINGFACE_API_KEY or leave empty for rate-limited access")
            print("   Get free key at: https://huggingface.co/settings/tokens")
            print("2. Google Gemini (FREE tier): Set GEMINI_API_KEY")
            print("   Get free key at: https://aistudio.google.com/")
            print("3. OpenAI (PAID): Set OPENAI_API_KEY")
            print("\nSet LLM_PROVIDER in your .env file to choose provider")
            return
        
        # Create and run the feed
        feed = ResearchPaperFeed()
        feed_data = feed.generate_daily_feed()
        feed.print_feed(feed_data)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()
