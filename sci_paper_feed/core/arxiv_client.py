"""Clean arXiv API client for fetching daily AI papers."""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import re
import logging
import config


class ArxivClient:
    """Clean arXiv API client for fetching papers by date and category."""
    
    def __init__(self, base_url: str = "http://export.arxiv.org/api/query"):
        self.base_url = base_url
        self.session = requests.Session()
        # arXiv API doesn't require special headers, but good to be respectful
        self.session.headers.update({
            'User-Agent': 'AI-Research-Feed/1.0 (Educational Project)'
        })
        self.logger = logging.getLogger(__name__)
    
    def fetch_daily_papers(self, category: str = None, target_date: datetime = None) -> List[Dict[str, str]]:
        """
        Fetch papers submitted on a specific date.
        
        Args:
            category: arXiv category (e.g., 'cs.AI', 'cs.LG')
            target_date: Date to fetch papers for (defaults to today)
        
        Returns:
            List of paper dictionaries with title, abstract, authors, etc.
        """
        if category is None:
            category = config.ARXIV_CATEGORY
        if target_date is None:
            target_date = datetime.now()
        
        self.logger.info(f"Fetching {category} papers for {target_date.strftime('%Y-%m-%d')}")
        self.logger.debug(f"Starting date: {target_date}")
        self.logger.debug(f"Category: {category}")
        

        search_date = target_date
        self.logger.debug(f"Trying date: {search_date.strftime('%Y-%m-%d')}")
        
        papers = self._fetch_by_announcement_date(category, search_date)
        
        if papers:
            self.logger.info(f"Found {len(papers)} papers for {search_date.strftime('%Y-%m-%d')}")
            return papers

        self.logger.info(f"No papers found for {search_date.strftime('%Y-%m-%d')}")
        return []
    

    def _fetch_by_announcement_date(self, category: str, target_date: datetime) -> List[Dict[str, str]]:
        """Fetch papers by announcement date (when they appear on arXiv)."""
        # Format dates for arXiv API (YYYYMMDDHHMM format)
        date_start = target_date.strftime("%Y%m%d0000")
        date_end = target_date.strftime("%Y%m%d2359")
        
        self.logger.debug(f"Date range: {date_start} TO {date_end}")
        
        # Build query using lastUpdatedDate which corresponds to announcement date
        query = f"cat:{category} AND lastUpdatedDate:[{date_start} TO {date_end}]"
        
        self.logger.debug(f"Announcement date query: {query}")
        
        papers = self._fetch_papers_with_query(query, f"announcement date {target_date.strftime('%Y-%m-%d')}")
        
        return papers
    

    
    def _fetch_papers_with_query(self, query: str, description: str) -> List[Dict[str, str]]:
        """Fetch papers using a specific query."""
        self.logger.debug(f"Searching for papers ({description}): {query}")
        
        papers = []
        start = 0
        max_results = 100  # arXiv API limit per request
        
        while True:
            params = {
                'search_query': query,
                'start': start,
                'max_results': max_results,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            try:
                self.logger.debug(f"Making API request with params: {params}")
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                self.logger.debug(f"API response status: {response.status_code}")
                self.logger.debug(f"API response length: {len(response.content)} bytes")
                
                # Parse XML response
                root = ET.fromstring(response.content)
                
                # Check for errors in the response
                error_elem = root.find('{http://www.w3.org/2005/Atom}error')
                if error_elem is not None:
                    self.logger.error(f"arXiv API error: {error_elem.text}")
                
                entries = root.findall('{http://www.w3.org/2005/Atom}entry')
                
                self.logger.debug(f"Found {len(entries)} entries in XML response")
                
                if not entries:
                    self.logger.debug("No entries found, breaking pagination loop")
                    break
                
                self.logger.debug(f"Processing {len(entries)} papers (batch {start//max_results + 1})")
                
                parsed_count = 0
                for i, entry in enumerate(entries):
                    paper_info = self._parse_api_entry(entry)
                    if paper_info:
                        papers.append(paper_info)
                        parsed_count += 1
                        self.logger.debug(f"Successfully parsed paper {i+1}: {paper_info['arxiv_id']}")
                    else:
                        self.logger.debug(f"Failed to parse paper {i+1}")
                
                self.logger.debug(f"Successfully parsed {parsed_count}/{len(entries)} papers")
                
                # If we got fewer than max_results, we've reached the end
                if len(entries) < max_results:
                    self.logger.debug("Got fewer entries than max_results, reached end")
                    break
                
                start += max_results
                
                # Be respectful to the API - don't hammer it
                if start > 0:
                    time.sleep(1)
                
                # Safety limit - don't fetch more than 1000 papers
                if start >= 1000:
                    self.logger.warning("Reached safety limit of 1000 papers")
                    self.logger.debug("Hit safety limit")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error fetching from arXiv API: {e}")
                self.logger.error(f"API request failed: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    self.logger.error(f"Response content: {e.response.content[:500]}")
                break
        
        return papers
    
    def _parse_api_entry(self, entry) -> Optional[Dict[str, str]]:
        """Parse a single entry from arXiv API XML response."""
        try:
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            # Extract arXiv ID
            id_elem = entry.find('atom:id', ns)
            if id_elem is None:
                return None
            
            arxiv_url = id_elem.text
            arxiv_id = arxiv_url.split('/')[-1]
            
            # Extract title and clean it up
            title_elem = entry.find('atom:title', ns)
            if title_elem is None:
                return None
            
            title = title_elem.text.strip()
            title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
            
            # Extract authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())
            
            authors_str = ", ".join(authors) if authors else "Unknown Authors"
            
            # Extract abstract and clean it up
            summary_elem = entry.find('atom:summary', ns)
            if summary_elem is None:
                return None
            
            abstract = summary_elem.text.strip()
            abstract = re.sub(r'\s+', ' ', abstract)  # Normalize whitespace
            
            # Extract categories/subjects
            categories = []
            for category in entry.findall('atom:category', ns):
                term = category.get('term')
                if term:
                    categories.append(term)
            
            subjects = ", ".join(categories) if categories else config.ARXIV_CATEGORY
            
            # Extract announcement date (when paper appeared on arXiv)
            updated_elem = entry.find('atom:updated', ns)
            announcement_date = updated_elem.text if updated_elem is not None else None
            
            # Also get submission date for reference
            published_elem = entry.find('atom:published', ns)
            submission_date = published_elem.text if published_elem is not None else None
            
            return {
                'arxiv_id': arxiv_id,
                'title': title,
                'authors': authors_str,
                'subjects': subjects,
                'abstract': abstract,
                'url': f"https://arxiv.org/abs/{arxiv_id}",
                'submission_date': submission_date,
                'announcement_date': announcement_date
            }
            
        except Exception as e:
            self.logger.warning(f"Error parsing API entry: {e}")
            return None
    

    
    def _deduplicate_papers(self, papers: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove duplicate papers based on arXiv ID."""
        seen_ids = set()
        deduplicated = []
        
        for paper in papers:
            arxiv_id = paper.get('arxiv_id')
            if arxiv_id and arxiv_id not in seen_ids:
                deduplicated.append(paper)
                seen_ids.add(arxiv_id)
        
        return deduplicated
    

