"""Database viewer page for the AI Research Paper Feed."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import List
import math
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import DatabaseManager
from services.paper_service import PaperService
from models.paper import Paper
import config


def show_database_viewer():
    """Display the database viewer page."""

    st.title("📊 Database Viewer")
    st.markdown("*Browse all papers in the database*")

    # Initialize services
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    if "paper_service" not in st.session_state:
        st.session_state.paper_service = PaperService()

    db = st.session_state.db_manager
    paper_service = st.session_state.paper_service

    # Get database statistics
    stats = db.get_database_stats()

    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Papers", stats["total_papers"])
    with col2:
        st.metric("Analyzed Papers", stats["analyzed_papers"])
    with col3:
        st.metric("Unanalyzed Papers", stats["unanalyzed_papers"])
    with col4:
        # Analysis progress wheel chart
        if stats["total_papers"] > 0:
            analyzed_pct = stats["analyzed_papers"] / stats["total_papers"] * 100

            # Create pie chart for analysis progress
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["Analyzed", "Unanalyzed"],
                        values=[stats["analyzed_papers"], stats["unanalyzed_papers"]],
                        hole=0.6,
                        marker_colors=["#00CC96", "#EF553B"],
                        textinfo="none",
                        showlegend=False,
                    )
                ]
            )

            fig.update_layout(
                title=f"Analysis Progress<br>{analyzed_pct:.1f}%",
                title_x=0.5,
                title_font_size=14,
                height=200,
                margin=dict(t=50, b=0, l=0, r=0),
            )

            # Add center text
            fig.add_annotation(
                text=f"{analyzed_pct:.1f}%", x=0.5, y=0.5, font_size=20, showarrow=False
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.metric("Analysis Progress", "0%")

    # Remove papers by field section as requested

    st.divider()

    # Filters
    col_field, col_per_page, _, col_analyze, col_reanalyze, col_purge = st.columns([1.5, 0.8, 1, 1.2, 1.4, 0.7])

    with col_field:
        field_options = ["All Fields"] + list(stats["field_counts"].keys())
        selected_field = st.selectbox("Field:", field_options)
        field_filter = None if selected_field == "All Fields" else selected_field

    with col_per_page:
        per_page = st.selectbox("Per page:", [25, 50, 100], index=2)

    fallback_count = len(db.get_all_fallback_papers())

    with col_analyze:
        st.write("")  # vertical align with dropdowns
        if st.button("🤖 Analyze", type="primary", use_container_width=True, help="Analyze all unanalyzed papers"):
            analyze_unanalyzed_papers(db, paper_service)

    with col_reanalyze:
        st.write("")
        if st.button(f"🔄 Reanalyze ({fallback_count})", use_container_width=True, help="Reanalyze all fallback-scored papers"):
            reanalyze_fallback_papers(db, paper_service)

    with col_purge:
        st.write("")
        if st.button("🗑️ Purge", type="secondary", use_container_width=True, help="⚠️ Delete ALL data!"):
            st.session_state.show_purge_dialog = True

    # Get papers with pagination
    page = st.session_state.get("db_page", 1)
    papers, total_count = db.get_all_papers_paginated(
        page=page, per_page=per_page, field=field_filter
    )

    if total_count == 0:
        st.info("No papers found in the database.")
        return

    # Pagination info
    total_pages = math.ceil(total_count / per_page)
    start_idx = (page - 1) * per_page + 1
    end_idx = min(page * per_page, total_count)

    st.subheader(f"📄 Papers {start_idx}-{end_idx} of {total_count}")

    # Pagination controls
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⏮️ First", disabled=(page == 1)):
            st.session_state.db_page = 1
            st.rerun()

    with col2:
        if st.button("◀️ Previous", disabled=(page == 1)):
            st.session_state.db_page = page - 1
            st.rerun()

    with col3:
        st.write(f"Page {page} of {total_pages}")

    with col4:
        if st.button("Next ▶️", disabled=(page == total_pages)):
            st.session_state.db_page = page + 1
            st.rerun()

    with col5:
        if st.button("Last ⏭️", disabled=(page == total_pages)):
            st.session_state.db_page = total_pages
            st.rerun()

    # Bulk fetch fields for all papers to display
    paper_ids = [paper.arxiv_id for paper in papers]
    papers_fields = db.get_papers_fields_bulk(paper_ids)

    # Check if we should show the purge dialog
    if st.session_state.get("show_purge_dialog", False):
        st.divider()
        st.subheader("🗑️ Purge Database")
        purge_database_with_confirmation(db, paper_service)
        return  # Don't show the rest of the page when purge dialog is active

    # Display papers
    for i, paper in enumerate(papers, start_idx):
        display_paper_row(paper, i, papers_fields.get(paper.arxiv_id, []))

    # Bottom pagination (same as top)
    st.divider()
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⏮️ First ", disabled=(page == 1), key="bottom_first"):
            st.session_state.db_page = 1
            st.rerun()

    with col2:
        if st.button("◀️ Previous ", disabled=(page == 1), key="bottom_prev"):
            st.session_state.db_page = page - 1
            st.rerun()

    with col3:
        st.write(f"Page {page} of {total_pages}")

    with col4:
        if st.button("Next ▶️ ", disabled=(page == total_pages), key="bottom_next"):
            st.session_state.db_page = page + 1
            st.rerun()

    with col5:
        if st.button("Last ⏭️ ", disabled=(page == total_pages), key="bottom_last"):
            st.session_state.db_page = total_pages
            st.rerun()


def display_paper_row(paper: Paper, index: int, paper_fields: List[str] = None):
    """Display a single paper row in the database viewer."""

    # Determine score display and color
    is_fallback = paper.analyzed and paper.analysis_type == "fallback"
    if paper.analyzed and paper.ai_score is not None:
        score_display = f"⭐ {paper.ai_score:.1f}/10"
        score_color = get_score_color(paper.ai_score)
        if is_fallback:
            score_display += " ⚠️ fallback"
    else:
        score_display = "⏳ Not analyzed"
        score_color = "gray"

    # Create expandable container for each paper
    with st.expander(
        f"#{index} - {paper.title[:80]}{'...' if len(paper.title) > 80 else ''} - :{score_color}[{score_display}]",
        expanded=False,
    ):
        # Paper details in columns
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Title:** {paper.title}")
            st.markdown(f"**Authors:** {paper.authors}")

            # Abstract
            with st.expander("📄 Abstract"):
                st.markdown(paper.abstract)

            # AI Analysis (if available)
            if paper.analyzed and paper.ai_explanation:
                st.markdown("**🤖 AI Analysis:**")
                st.markdown(paper.ai_explanation)

                if paper.ai_key_insights:
                    with st.expander("🔍 Key Insights"):
                        st.markdown(paper.ai_key_insights)

        with col2:
            # Metadata
            # Use provided fields or fetch them if not provided
            if paper_fields is not None:
                fields_display = ", ".join(paper_fields) if paper_fields else "Unknown"
            else:
                # Fallback to individual query (for backward compatibility)
                fetched_fields = st.session_state.db_manager.get_paper_fields(
                    paper.arxiv_id
                )
                fields_display = (
                    ", ".join(fetched_fields) if fetched_fields else "Unknown"
                )
            st.markdown(f"**Fields:** {fields_display}")
            st.markdown(f"**arXiv ID:** {paper.arxiv_id}")

            if paper.date_announced:
                st.markdown(
                    f"**Announced:** {paper.date_announced.strftime('%Y-%m-%d %H:%M')}"
                )

            if paper.date_submitted:
                st.markdown(
                    f"**Submitted:** {paper.date_submitted.strftime('%Y-%m-%d %H:%M')}"
                )

            if paper.date_added:
                st.markdown(
                    f"**Added to DB:** {paper.date_added.strftime('%Y-%m-%d %H:%M')}"
                )

            # arXiv link
            st.link_button(
                "📄 View on arXiv", paper.arxiv_url, use_container_width=True
            )

            # Analyze / Reanalyze buttons
            if not paper.analyzed:
                if st.button("🤖 Analyze", key=f"analyze_{paper.arxiv_id}", use_container_width=True):
                    _analyze_single_paper(paper, st.session_state.db_manager, st.session_state.paper_service)
            elif is_fallback:
                if st.button("🔄 Reanalyze", key=f"reanalyze_{paper.arxiv_id}", use_container_width=True):
                    _analyze_single_paper(paper, st.session_state.db_manager, st.session_state.paper_service)


def _analyze_single_paper(paper: Paper, db: DatabaseManager, paper_service: PaperService):
    """Analyze a single paper and update the database."""
    with st.spinner(f"Analyzing: {paper.title[:60]}..."):
        try:
            paper_data = {
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "url": paper.arxiv_url,
                "subjects": paper.subjects or "",
            }
            analyzed = paper_service.analyzer._analyze_paper_batch([paper_data])
            if analyzed:
                db.update_paper_analysis(
                    paper.arxiv_id,
                    {
                        "score": analyzed[0].get("score"),
                        "explanation": analyzed[0].get("explanation"),
                        "key_insights": analyzed[0].get("key_insights"),
                        "analysis_type": analyzed[0].get("analysis_type", "llm"),
                    },
                )
                st.success(f"Analyzed! Score: {analyzed[0].get('score')}/10")
                st.rerun()
            else:
                st.error("Analysis returned no results.")
        except Exception as e:
            st.error(f"Error analyzing paper: {e}")


def analyze_unanalyzed_papers(db: DatabaseManager, paper_service: PaperService):
    """Analyze all unanalyzed papers in the database."""

    # Get all unanalyzed papers
    unanalyzed_papers = db.get_all_unanalyzed_papers()

    if not unanalyzed_papers:
        st.success("🎉 All papers are already analyzed!")
        return

    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()

    total_papers = len(unanalyzed_papers)
    status_text.text(f"Starting analysis of {total_papers} papers...")

    # Convert Paper objects to dict format for analyzer
    papers_data = []
    for paper in unanalyzed_papers:
        papers_data.append(
            {
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "url": paper.arxiv_url,
                "subjects": paper.subjects,
            }
        )

    # Analyze papers in batches
    batch_size = config.ANALYSIS_BATCH_SIZE
    analyzed_count = 0

    for i in range(0, len(papers_data), batch_size):
        batch = papers_data[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(papers_data) + batch_size - 1) // batch_size

        status_text.text(
            f"Analyzing batch {batch_num}/{total_batches} ({len(batch)} papers)..."
        )

        try:
            # Analyze the batch
            analyzed_papers, _ = paper_service.analyzer.analyze_and_rank_papers(
                batch, len(batch)
            )

            # Update database with results
            for analyzed_paper in analyzed_papers:
                try:
                    db.update_paper_analysis(
                        analyzed_paper["arxiv_id"],
                        {
                            "score": analyzed_paper.get("score"),
                            "explanation": analyzed_paper.get("explanation"),
                            "key_insights": analyzed_paper.get("key_insights"),
                            "analysis_type": analyzed_paper.get("analysis_type", "llm"),
                        },
                    )
                    analyzed_count += 1
                except Exception as e:
                    st.error(f"Error updating paper {analyzed_paper['arxiv_id']}: {e}")

            # Update progress
            progress = (i + len(batch)) / len(papers_data)
            progress_bar.progress(progress)

        except Exception as e:
            st.error(f"Error analyzing batch {batch_num}: {e}")

    # Complete
    progress_bar.progress(1.0)
    status_text.text(
        f"✅ Analysis complete! Successfully analyzed {analyzed_count} papers."
    )

    # Show success message
    if analyzed_count > 0:
        st.success(f"🎉 Successfully analyzed {analyzed_count} papers!")
        st.balloons()

        # Refresh the page to show updated stats
        st.rerun()
    else:
        st.warning("⚠️ No papers were successfully analyzed.")


def reanalyze_fallback_papers(db: DatabaseManager, paper_service: PaperService):
    """Reanalyze all papers that previously received fallback scoring."""
    fallback_papers = db.get_all_fallback_papers()

    if not fallback_papers:
        st.success("No fallback-scored papers found!")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(fallback_papers)
    status_text.text(f"Reanalyzing {total} fallback-scored papers...")

    papers_data = [
        {
            "arxiv_id": p.arxiv_id,
            "title": p.title,
            "authors": p.authors,
            "abstract": p.abstract,
            "url": p.arxiv_url,
            "subjects": p.subjects or "",
        }
        for p in fallback_papers
    ]

    batch_size = config.ANALYSIS_BATCH_SIZE
    analyzed_count = 0

    for i in range(0, len(papers_data), batch_size):
        batch = papers_data[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(papers_data) + batch_size - 1) // batch_size
        status_text.text(f"Analyzing batch {batch_num}/{total_batches} ({len(batch)} papers)...")

        try:
            analyzed_papers, _ = paper_service.analyzer.analyze_and_rank_papers(batch, len(batch))
            for analyzed_paper in analyzed_papers:
                try:
                    db.update_paper_analysis(
                        analyzed_paper["arxiv_id"],
                        {
                            "score": analyzed_paper.get("score"),
                            "explanation": analyzed_paper.get("explanation"),
                            "key_insights": analyzed_paper.get("key_insights"),
                            "analysis_type": analyzed_paper.get("analysis_type", "llm"),
                        },
                    )
                    analyzed_count += 1
                except Exception as e:
                    st.error(f"Error updating {analyzed_paper['arxiv_id']}: {e}")
        except Exception as e:
            st.error(f"Error analyzing batch {batch_num}: {e}")

        progress_bar.progress((i + len(batch)) / len(papers_data))

    progress_bar.progress(1.0)
    status_text.text(f"Done! Reanalyzed {analyzed_count}/{total} papers.")
    if analyzed_count > 0:
        st.success(f"Successfully reanalyzed {analyzed_count} papers!")
        st.rerun()
    else:
        st.warning("No papers were successfully reanalyzed.")


def purge_database_with_confirmation(db: DatabaseManager, paper_service):
    """Purge database with confirmation dialog."""
    st.warning(
        "⚠️ **WARNING**: This will permanently delete ALL papers, fields, and analysis data from the database!"
    )
    st.write("This action cannot be undone.")
    st.write("**Are you absolutely sure you want to proceed?**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "✅ Yes, DELETE Everything", type="primary", key="confirm_purge_final"
        ):
            st.write("🔄 Button clicked - starting purge...")

            with st.spinner("Purging database..."):
                try:

                    # Call database purge directly to avoid LLM initialization issues
                    result = db.purge_database()

                    st.success(f"✅ Database purged successfully!")
                    st.write(f"**Deleted:**")
                    st.write(f"- {result['papers_deleted']} papers")
                    st.write(f"- {result['fields_deleted']} fields")
                    st.write(f"- {result['associations_deleted']} field associations")

                    # Clear the dialog state and refresh
                    st.session_state.show_purge_dialog = False
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error purging database: {e}")

    with col2:
        if st.button("❌ Cancel", type="secondary", key="cancel_purge_final"):
            st.session_state.show_purge_dialog = False
            st.info("Database purge cancelled.")
            st.rerun()


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
    show_database_viewer()
