"""Service layer for paper analysis and database operations."""

from datetime import datetime, timedelta
from typing import List, Dict
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import DatabaseManager
from models.paper import Paper
from core.paper_analyzer import PaperAnalyzer
from core.arxiv_client import ArxivClient
import config

class PaperService:
    """Service for managing paper analysis and database operations."""
    
    def __init__(self, db_path: str = None):
        self.db = DatabaseManager(db_path)
        self.arxiv_client = ArxivClient()
        self.analyzer = PaperAnalyzer()
        self.logger = logging.getLogger(__name__)
    
    def refresh_papers_for_field(self, field: str) -> Dict:
        """
        Refresh papers for a specific field by analyzing new papers since last update.
        
        Args:
            field: arXiv field (e.g., 'cs.AI', 'hep-th')
            
        Returns:
            Dict with statistics about the refresh operation
        """
        self.logger.info(f"Starting refresh for field: {field}")
        
        # Get last analyzed date
        last_date = self.db.get_last_analyzed_date(field)
        today = datetime.now()
        
        self.logger.info(f"Last analyzed date for {field}: {last_date.strftime('%Y-%m-%d')}")
        
        # Determine date range to analyze
        start_date = last_date
       
        
        stats = {
            'field': field,
            'last_analyzed': last_date,
            'date_range_start': start_date,
            'date_range_end': today,
            'new_papers_found': 0,
            'papers_analyzed': 0,
            'papers_added': 0,
            'errors': []
        }
        
        # Fetch and analyze papers for each day in the range, newest-first,
        # stopping once we reach MAX_PAPERS_LOOKBACK total analyses.
        total_analyzed_this_run = 0
        current_date = today
        while current_date >= start_date:
            if total_analyzed_this_run >= config.MAX_PAPERS_LOOKBACK:
                self.logger.info(
                    f"Reached MAX_PAPERS_LOOKBACK ({config.MAX_PAPERS_LOOKBACK}), stopping refresh."
                )
                break

            try:
                self.logger.info(f"Processing papers for {current_date.strftime('%Y-%m-%d')}")

                papers = self.arxiv_client.fetch_daily_papers(category=field, target_date=current_date)

                if papers:
                    stats['new_papers_found'] += len(papers)

                    for paper_data in papers:
                        try:
                            was_added = self.db.add_paper(paper_data)
                            if was_added:
                                stats['papers_added'] += 1
                        except Exception as e:
                            self.logger.error(f"Error adding paper {paper_data.get('arxiv_id', 'unknown')}: {e}")
                            stats['errors'].append(f"Error adding paper: {e}")

                    unanalyzed_papers = [p for p in papers if not self._is_paper_analyzed(p['arxiv_id'])]
                    if unanalyzed_papers:
                        remaining = config.MAX_PAPERS_LOOKBACK - total_analyzed_this_run
                        cap = min(config.MAX_PAPERS_TO_ANALYZE, remaining)
                        if len(unanalyzed_papers) > cap:
                            self.logger.info(f"Capping analysis at {cap} of {len(unanalyzed_papers)} papers for this date")
                            unanalyzed_papers = unanalyzed_papers[:cap]

                        self.logger.info(f"Analyzing {len(unanalyzed_papers)} papers")
                        analyzed_papers = self._analyze_papers_batch(unanalyzed_papers)

                        for analyzed_paper in analyzed_papers:
                            try:
                                was_updated = self.db.update_paper_analysis(
                                    analyzed_paper['arxiv_id'],
                                    {
                                        'score': analyzed_paper.get('score'),
                                        'explanation': analyzed_paper.get('explanation'),
                                        'key_insights': analyzed_paper.get('key_insights'),
                                        'analysis_type': analyzed_paper.get('analysis_type', 'llm'),
                                    }
                                )
                                if was_updated:
                                    stats['papers_analyzed'] += 1
                                    total_analyzed_this_run += 1
                            except Exception as e:
                                self.logger.error(f"Error updating analysis for {analyzed_paper['arxiv_id']}: {e}")
                                stats['errors'].append(f"Error updating analysis: {e}")

                current_date -= timedelta(days=1)

            except Exception as e:
                self.logger.error(f"Error processing date {current_date}: {e}")
                stats['errors'].append(f"Error processing {current_date.strftime('%Y-%m-%d')}: {e}")
                current_date -= timedelta(days=1)
        
        self.logger.info(f"Refresh completed. Analyzed {stats['papers_analyzed']} papers")
        return stats
    
    def get_papers_for_display(self, field: str, days_back: int = None) -> Dict[str, List[Paper]]:
        """
        Get papers organized by date for display.
        
        Args:
            field: arXiv field
            days_back: Number of days back to fetch (uses config.DAYS_TO_DISPLAY if None)
            
        Returns:
            Dict mapping date strings to lists of papers
        """
        if days_back is None:
            days_back = config.DAYS_TO_DISPLAY
            
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back - 1)
        
        papers_by_date = {}
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            papers = self.db.get_papers_by_field_and_date(field, current_date)
            
            # Only include dates that have papers
            if papers:
                papers_by_date[date_str] = papers
            
            current_date += timedelta(days=1)
        
        return papers_by_date
    
    def get_available_fields(self) -> List[str]:
        """Get list of available fields from config."""
        return config.AVAILABLE_FIELDS
    
    def purge_database(self) -> Dict[str, int]:
        """
        Purge all data from the database.
        
        Returns:
            Dict with counts of deleted records
        """
        self.logger.info("Purging database...")
        try:
            result = self.db.purge_database()
            self.logger.info(f"Database purged successfully: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error purging database: {e}")
            raise e
    
    def _is_paper_analyzed(self, arxiv_id: str) -> bool:
        """Check if a paper has been analyzed."""
        session = self.db.get_session()
        try:
            paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
            return paper and paper.analyzed
        finally:
            session.close()
    
    def _analyze_papers_batch(self, papers: List[Dict]) -> List[Dict]:
        """Analyze a batch of papers using the paper analyzer."""
        try:
            # Use the existing paper analyzer
            analyzed_papers, _ = self.analyzer.analyze_and_rank_papers(papers, len(papers))
            return analyzed_papers
        except Exception as e:
            self.logger.error(f"Error in batch analysis: {e}")
            # Return papers with default analysis if analysis fails
            return [{
                **paper,
                'score': 5,
                'explanation': 'Analysis failed - default score assigned',
                'key_insights': 'Analysis unavailable due to error',
                'analysis_type': 'fallback',
            } for paper in papers]
