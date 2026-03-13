"""Ranked Feed page — best papers of the current calendar year per category."""

import streamlit as st
from datetime import datetime
from typing import List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.paper import Paper
import config


def show_ranked_feed():
    """Display the ranked feed page."""

    st.title("🏆 Ranked Feed")
    st.markdown("*Best papers of the year, ranked by AI score*")

    if "paper_service" not in st.session_state:
        from services.paper_service import PaperService
        st.session_state.paper_service = PaperService()

    db = st.session_state.paper_service.db

    col1, col2 = st.columns([2, 1])

    with col1:
        available_fields = config.AVAILABLE_FIELDS
        selected_field = st.selectbox("Select Field:", available_fields, index=0)

    with col2:
        current_year = datetime.now().year
        selected_year = st.selectbox("Year:", list(range(current_year, current_year - 5, -1)), index=0)

    st.divider()

    papers = db.get_top_papers_for_year(selected_field, selected_year, limit=100)

    if not papers:
        st.info(f"No analyzed papers found for {selected_field} in {selected_year}. Use the Daily Feed to fetch and analyze papers first.")
        return

    st.subheader(f"Top {len(papers)} papers — {selected_field} — {selected_year}")

    paper_ids = [p.arxiv_id for p in papers]
    papers_fields = db.get_papers_fields_bulk(paper_ids)

    for i, paper in enumerate(papers, 1):
        _display_ranked_paper(paper, i, papers_fields.get(paper.arxiv_id, []))


def _display_ranked_paper(paper: Paper, rank: int, paper_fields: List[str]):
    """Display a single paper card in the ranked feed."""
    score = paper.ai_score
    score_color = _score_color(score)
    score_str = f"{score:.1f}/10"
    if paper.analysis_type == "fallback":
        score_str += " ⚠️ fallback"

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.markdown(f"**#{rank}**")
        with col2:
            st.markdown(f":{score_color}[⭐ **{score_str}**]")
        with col3:
            st.link_button("📄 arXiv", paper.arxiv_url, use_container_width=True)

        st.markdown(f"### {paper.title}")
        st.markdown(f"**Authors:** {paper.authors}")

        if paper.ai_explanation:
            st.markdown("**🤖 AI Analysis:**")
            st.markdown(paper.ai_explanation)
            if paper.ai_key_insights:
                with st.expander("🔍 Key Insights"):
                    st.markdown(paper.ai_key_insights)

        with st.expander("📄 Abstract"):
            st.markdown(paper.abstract)

        col1, col2 = st.columns(2)
        with col1:
            fields_display = ", ".join(paper_fields) if paper_fields else "Unknown"
            st.caption(f"**Fields:** {fields_display}")
        with col2:
            if paper.date_announced:
                st.caption(f"**Announced:** {paper.date_announced.strftime('%Y-%m-%d')}")

        st.divider()


def _score_color(score: float) -> str:
    if score >= 8:
        return "green"
    elif score >= 6:
        return "blue"
    elif score >= 4:
        return "orange"
    return "red"
