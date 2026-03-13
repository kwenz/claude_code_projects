"""Streamlit web interface for the AI Research Paper Feed."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.paper_service import PaperService
from models.paper import Paper
import config

# Import page modules
try:
    from app.database_viewer import show_database_viewer
    from app.ranked_feed import show_ranked_feed
except ImportError:
    import importlib.util

    def _load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, os.path.join(os.path.dirname(__file__), path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    show_database_viewer = _load_module("database_viewer", "database_viewer.py").show_database_viewer
    show_ranked_feed = _load_module("ranked_feed", "ranked_feed.py").show_ranked_feed

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="AI Research Paper Feed",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'paper_service' not in st.session_state:
    st.session_state.paper_service = PaperService()

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None

if 'refresh_stats' not in st.session_state:
    st.session_state.refresh_stats = None


def main():
    """Main application function."""
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🧠 AI Research Paper Feed")
        page = st.radio(
            "Navigate to:",
            ["📊 Daily Feed", "🏆 Ranked Feed", "🗄️ Database Viewer"],
            index=0
        )

    if page == "📊 Daily Feed":
        show_daily_feed()
    elif page == "🏆 Ranked Feed":
        show_ranked_feed()
    elif page == "🗄️ Database Viewer":
        show_database_viewer()


def show_daily_feed():
    """Show the main daily feed page."""
    
    # Header
    st.title("📊 Daily Research Paper Feed")
    st.markdown("*Discover the most interesting research papers, analyzed by AI*")
    
    # Controls row
    col1, col2, col3, col4 = st.columns([2, 1, 1, 4])
    
    with col1:
        # Field selection dropdown
        available_fields = st.session_state.paper_service.get_available_fields()
        selected_field = st.selectbox(
            "Select Field:",
            available_fields,
            index=0,
            help="Choose the arXiv field to analyze"
        )
    
    with col2:
        # Refresh button
        if st.button("🔄 Refresh", type="primary", help="Fetch and analyze new papers"):
            refresh_papers(selected_field)
    
    with col3:
        # Show refresh status
        if st.session_state.last_refresh:
            st.success(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M')}")
    
    with col4:
        # Show refresh stats if available
        if st.session_state.refresh_stats:
            stats = st.session_state.refresh_stats
            if stats['errors']:
                st.warning(f"⚠️ {len(stats['errors'])} errors occurred")
            else:
                st.info(f"✅ Analyzed {stats['papers_analyzed']} papers, added {stats['papers_added']} new")
    
    st.divider()
    
    # Display papers
    display_papers(selected_field)


def refresh_papers(field: str):
    """Refresh papers for the selected field."""
    with st.spinner(f"Refreshing papers for {field}..."):
        try:
            stats = st.session_state.paper_service.refresh_papers_for_field(field)
            st.session_state.last_refresh = datetime.now()
            st.session_state.refresh_stats = stats
            
            if stats['errors']:
                st.error(f"Refresh completed with {len(stats['errors'])} errors. Check logs for details.")
            else:
                st.success(f"Successfully refreshed! Analyzed {stats['papers_analyzed']} papers.")
            
            # Force rerun to update display
            st.rerun()
            
        except Exception as e:
            st.error(f"Error during refresh: {e}")
            logging.error(f"Refresh error: {e}")


def display_papers(field: str):
    """Display papers organized by date."""
    # Get papers for the configured number of days
    papers_by_date = st.session_state.paper_service.get_papers_for_display(field, days_back=config.DAYS_TO_DISPLAY)
    
    if not papers_by_date:
        st.info(f"No papers found for {field}. Click 'Refresh' to fetch and analyze papers.")
        return
    
    # Display papers by date (most recent first)
    sorted_dates = sorted(papers_by_date.keys(), reverse=True)
    
    for date_str in sorted_dates:
        papers = papers_by_date[date_str]
        
        # Create expandable section for each date
        with st.expander(
            f"📅 **{date_str}** - {len(papers)} papers", 
            expanded=(date_str == sorted_dates[0])  # Expand most recent day by default
        ):
            display_papers_for_date(papers, date_str)


def display_papers_for_date(papers: list, date_str: str):
    """Display papers for a specific date."""
    if not papers:
        st.info("No papers for this date.")
        return
    
    # Sort papers by score (highest first), with unanalyzed papers at the end
    analyzed_papers = [p for p in papers if p.analyzed and p.ai_score is not None]
    unanalyzed_papers = [p for p in papers if not p.analyzed or p.ai_score is None]
    
    sorted_papers = sorted(analyzed_papers, key=lambda x: x.ai_score, reverse=True) + unanalyzed_papers
    
    # Limit to TOP_PAPERS_COUNT
    top_papers = sorted_papers[:config.TOP_PAPERS_COUNT]
    
    # Show info if there are more papers than displayed
    if len(sorted_papers) > config.TOP_PAPERS_COUNT:
        st.info(f"Showing top {config.TOP_PAPERS_COUNT} of {len(sorted_papers)} papers for this date.")
    
    # Bulk fetch fields for all papers to display
    paper_ids = [paper.arxiv_id for paper in top_papers]
    papers_fields = st.session_state.paper_service.db.get_papers_fields_bulk(paper_ids)
    
    for i, paper in enumerate(top_papers, 1):
        display_paper_card(paper, i, papers_fields.get(paper.arxiv_id, []))


def display_paper_card(paper: Paper, rank: int, paper_fields: List[str] = None):
    """Display a single paper as a card."""
    # Determine score display
    if paper.analyzed and paper.ai_score is not None:
        score_display = f"⭐ **{paper.ai_score:.1f}/10**"
        if paper.analysis_type == "fallback":
            score_display += " ⚠️ *fallback*"
        score_color = get_score_color(paper.ai_score)
    else:
        score_display = "⏳ *Not analyzed*"
        score_color = "gray"
    
    # Create paper card
    with st.container():
        # Header row with rank, score, and arXiv link
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.markdown(f"**#{rank}**")
        
        with col2:
            st.markdown(f":{score_color}[{score_display}]")
        
        with col3:
            st.link_button("📄 arXiv", paper.arxiv_url, use_container_width=True)
        
        # Title
        st.markdown(f"### {paper.title}")
        
        # Authors
        st.markdown(f"**Authors:** {paper.authors}")
        
        # AI Analysis (if available)
        if paper.analyzed and paper.ai_explanation:
            st.markdown("**🤖 AI Analysis:**")
            st.markdown(paper.ai_explanation)
            
            if paper.ai_key_insights:
                with st.expander("🔍 Key Insights"):
                    st.markdown(paper.ai_key_insights)
        
        # Abstract (collapsible)
        with st.expander("📄 Abstract"):
            st.markdown(paper.abstract)
        
        # Metadata
        col1, col2 = st.columns(2)
        with col1:
            # Use provided fields or fetch them if not provided
            if paper_fields is not None:
                fields_display = ", ".join(paper_fields) if paper_fields else "Unknown"
            else:
                # Fallback to individual query (for backward compatibility)
                fetched_fields = st.session_state.paper_service.db.get_paper_fields(paper.arxiv_id)
                fields_display = ", ".join(fetched_fields) if fetched_fields else "Unknown"
            st.caption(f"**Fields:** {fields_display}")
        with col2:
            if paper.date_announced:
                st.caption(f"**Announced:** {paper.date_announced.strftime('%Y-%m-%d')}")
        
        st.divider()


def get_score_color(score: float) -> str:
    """Get color for score display."""
    if score >= 8:
        return "green"
    elif score >= 6:
        return "blue"
    elif score >= 4:
        return "orange"
    else:
        return "red"


if __name__ == "__main__":
    main()
