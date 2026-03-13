"""Database service for managing paper data."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, joinedload
from datetime import datetime, timedelta
from typing import List, Dict

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import Base
from models.paper import Paper
from models.field import Field
from models.paper_field import PaperField
import config


class DatabaseManager:
    """Manages database operations for the paper feed."""

    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        if db_path is None:
            db_path = config.DATABASE_PATH
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._run_migrations()

    def _run_migrations(self):
        """Apply any schema changes not handled by create_all (e.g. new columns on existing tables)."""
        with self.engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE papers ADD COLUMN analysis_type VARCHAR(20)"))
                conn.commit()
            except Exception:
                pass  # Column already exists

            # Backfill analysis_type for pre-existing rows
            conn.execute(text("""
                UPDATE papers SET analysis_type = 'fallback'
                WHERE analyzed = 1
                  AND analysis_type IS NULL
                  AND (
                      ai_key_insights LIKE '%Unable to perform detailed analysis%'
                      OR ai_explanation LIKE '%Analysis unavailable%'
                      OR ai_explanation LIKE '%Analysis failed%'
                      OR ai_explanation LIKE '%Analysis based on title keywords%'
                  )
            """))
            conn.execute(text("""
                UPDATE papers SET analysis_type = 'llm'
                WHERE analyzed = 1 AND analysis_type IS NULL
            """))
            conn.commit()

    def get_session(self):
        """Get a database session."""
        return self.Session()

    def add_paper(self, paper_data: dict) -> bool:
        """Add a new paper to the database. Returns True if added, False if already exists."""
        session = self.get_session()
        try:
            # Check if paper already exists
            existing = (
                session.query(Paper).filter_by(arxiv_id=paper_data["arxiv_id"]).first()
            )
            if existing:
                # Make sure to detach the existing object from session before returning
                session.expunge(existing)
                return False  # Already exists

            # Create new paper
            paper = Paper(
                arxiv_id=paper_data["arxiv_id"],
                title=paper_data["title"],
                authors=paper_data["authors"],
                abstract=paper_data["abstract"],
                arxiv_url=paper_data["url"],
                subjects=paper_data.get("subjects", ""),
                date_announced=self._parse_date(paper_data.get("announcement_date")),
                date_submitted=self._parse_date(paper_data.get("submission_date")),
                ai_score=paper_data.get("score"),
                ai_explanation=paper_data.get("explanation"),
                ai_key_insights=paper_data.get("key_insights"),
                analyzed=paper_data.get("score") is not None,
            )

            session.add(paper)
            session.flush()  # Flush to get the paper in the session

            # Add field associations
            fields = self._extract_fields_from_subjects(paper_data.get("subjects", ""))
            for i, field_code in enumerate(fields):
                # Ensure field exists
                field = session.query(Field).filter_by(code=field_code).first()
                if not field:
                    field = Field(code=field_code, name=field_code)
                    session.add(field)
                    session.flush()

                # Create association
                association = PaperField(
                    paper_id=paper.arxiv_id, field_code=field_code, is_primary=(i == 0)
                )
                session.add(association)

            session.commit()
            # Expunge the paper from session to prevent detached instance issues
            session.expunge(paper)
            return True  # Successfully added

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_paper_analysis(self, arxiv_id: str, analysis_data: dict) -> bool:
        """Update a paper with analysis results. Returns True if updated successfully."""
        session = self.get_session()
        try:
            paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
            if not paper:
                raise ValueError(f"Paper {arxiv_id} not found")

            paper.ai_score = analysis_data.get("score")
            paper.ai_explanation = analysis_data.get("explanation")
            paper.ai_key_insights = analysis_data.get("key_insights")
            paper.analysis_type = analysis_data.get("analysis_type", "llm")
            paper.analyzed = True

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_papers_by_field_and_date_range(
        self, field: str, start_date: datetime, end_date: datetime
    ) -> List[Paper]:
        """Get papers by field within a date range."""
        session = self.get_session()
        try:
            papers = (
                session.query(Paper)
                .join(PaperField)
                .filter(
                    PaperField.field_code == field,
                    Paper.date_announced >= start_date,
                    Paper.date_announced <= end_date,
                )
                .order_by(
                    Paper.ai_score.desc().nullslast(), Paper.date_announced.desc()
                )
                .all()
            )

            # Expunge all papers from session to prevent detached instance issues
            for paper in papers:
                session.expunge(paper)

            return papers
        finally:
            session.close()

    def get_papers_by_field_and_date(self, field: str, date: datetime) -> List[Paper]:
        """Get papers by field for a specific date."""
        session = self.get_session()
        try:
            # Get papers announced on this date
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)

            papers = (
                session.query(Paper)
                .join(PaperField)
                .filter(
                    PaperField.field_code == field,
                    Paper.date_announced >= start_of_day,
                    Paper.date_announced <= end_of_day,
                )
                .order_by(Paper.ai_score.desc().nullslast())
                .all()
            )

            # Expunge all papers from session to prevent detached instance issues
            for paper in papers:
                session.expunge(paper)

            return papers
        finally:
            session.close()

    def get_last_analyzed_date(self, field: str) -> datetime:
        """Get the last date when papers were analyzed for a field."""
        session = self.get_session()
        try:
            result = (
                session.query(Paper.date_announced)
                .join(PaperField)
                .filter(PaperField.field_code == field, Paper.analyzed == True)
                .order_by(Paper.date_announced.desc())
                .first()
            )

            if result:
                return result[0]
            else:
                # If no analyzed papers, return a date far in the past
                return datetime.now() - timedelta(days=2)
        finally:
            session.close()

    def get_unanalyzed_papers(self, field: str = None) -> List[Paper]:
        """Get papers that haven't been analyzed yet."""
        session = self.get_session()
        try:
            query = session.query(Paper).filter(Paper.analyzed == False)
            if field:
                query = query.join(PaperField).filter(PaperField.field_code == field)
            papers = query.all()

            # Expunge all papers from session to prevent detached instance issues
            for paper in papers:
                session.expunge(paper)

            return papers
        finally:
            session.close()

    def get_all_papers_paginated(
        self, page: int = 1, per_page: int = 100, field: str = None
    ) -> tuple[List[Paper], int]:
        """Get all papers with pagination. Returns (papers, total_count)."""
        session = self.get_session()
        try:
            # Base query
            query = session.query(Paper)
            if field:
                # Join with PaperField to filter by field
                query = query.join(PaperField).filter(PaperField.field_code == field)

            # Get total count
            total_count = query.count()

            # Apply pagination and ordering
            papers = (
                query.order_by(
                    Paper.date_announced.desc(), Paper.ai_score.desc().nullslast()
                )
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )

            # Expunge all papers from session to prevent detached instance issues
            for paper in papers:
                session.expunge(paper)

            return papers, total_count
        finally:
            session.close()

    def get_database_stats(self) -> dict:
        """Get database statistics."""
        session = self.get_session()
        try:
            total_papers = session.query(Paper).count()
            analyzed_papers = (
                session.query(Paper).filter(Paper.analyzed == True).count()
            )

            # Get papers by field using the new many-to-many relationship
            field_counts = {}
            fields = session.query(Field).all()
            for field in fields:
                # Count papers associated with this field
                count = (
                    session.query(Paper)
                    .join(PaperField)
                    .filter(PaperField.field_code == field.code)
                    .count()
                )
                if count > 0:  # Only include fields that have papers
                    field_counts[field.code] = count

            return {
                "total_papers": total_papers,
                "analyzed_papers": analyzed_papers,
                "unanalyzed_papers": total_papers - analyzed_papers,
                "field_counts": field_counts,
            }
        finally:
            session.close()

    def get_top_papers_for_year(self, field: str, year: int, limit: int = 50) -> List[Paper]:
        """Get top analyzed papers for a given field and calendar year, ordered by score."""
        session = self.get_session()
        try:
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31, 23, 59, 59)
            papers = (
                session.query(Paper)
                .join(PaperField)
                .filter(
                    PaperField.field_code == field,
                    Paper.analyzed == True,
                    Paper.ai_score.isnot(None),
                    Paper.date_announced >= start,
                    Paper.date_announced <= end,
                )
                .order_by(Paper.ai_score.desc())
                .limit(limit)
                .all()
            )
            for paper in papers:
                session.expunge(paper)
            return papers
        finally:
            session.close()

    def get_all_fallback_papers(self) -> List[Paper]:
        """Get all papers that were analyzed with fallback scoring and need proper reanalysis."""
        session = self.get_session()
        try:
            papers = (
                session.query(Paper)
                .filter(Paper.analyzed == True, Paper.analysis_type == "fallback")
                .all()
            )
            for paper in papers:
                session.expunge(paper)
            return papers
        finally:
            session.close()

    def get_all_unanalyzed_papers(self) -> List[Paper]:
        """Get all unanalyzed papers for batch analysis."""
        session = self.get_session()
        try:
            papers = session.query(Paper).filter(Paper.analyzed == False).all()

            # Expunge all papers from session to prevent detached instance issues
            for paper in papers:
                session.expunge(paper)

            return papers
        finally:
            session.close()

    def get_all_papers(
        self, limit: int = 100, offset: int = 0, field: str = None
    ) -> List[Paper]:
        """Get all papers with pagination."""
        session = self.get_session()
        try:
            query = session.query(Paper)
            if field:
                query = query.join(PaperField).filter(PaperField.field_code == field)

            papers = (
                query.order_by(Paper.date_added.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            # Expunge all papers from session to prevent detached instance issues
            for paper in papers:
                session.expunge(paper)

            return papers
        finally:
            session.close()

    def get_paper_count(self, field: str = None) -> int:
        """Get total count of papers."""
        session = self.get_session()
        try:
            query = session.query(Paper)
            if field:
                query = query.join(PaperField).filter(PaperField.field_code == field)
            return query.count()
        finally:
            session.close()

    def get_paper_fields(self, arxiv_id: str) -> List[str]:
        """Get all field codes for a paper."""
        session = self.get_session()
        try:
            field_codes = (
                session.query(PaperField.field_code)
                .filter(PaperField.paper_id == arxiv_id)
                .all()
            )
            return [code[0] for code in field_codes]
        finally:
            session.close()

    def get_papers_fields_bulk(self, arxiv_ids: List[str]) -> Dict[str, List[str]]:
        """Get all field codes for multiple papers in one query."""
        session = self.get_session()
        try:
            # Get all paper-field associations for the given papers
            associations = (
                session.query(PaperField.paper_id, PaperField.field_code)
                .filter(PaperField.paper_id.in_(arxiv_ids))
                .all()
            )

            # Group by paper_id
            papers_fields = {}
            for paper_id, field_code in associations:
                if paper_id not in papers_fields:
                    papers_fields[paper_id] = []
                papers_fields[paper_id].append(field_code)

            # Ensure all papers have an entry (even if empty)
            for arxiv_id in arxiv_ids:
                if arxiv_id not in papers_fields:
                    papers_fields[arxiv_id] = []

            return papers_fields
        finally:
            session.close()

    def purge_database(self) -> Dict[str, int]:
        """
        Purge all data from the database.

        Returns:
            Dict with counts of deleted records
        """
        session = self.get_session()
        try:
            # Count records before deletion
            paper_count = session.query(Paper).count()
            field_count = session.query(Field).count()
            paper_field_count = session.query(PaperField).count()

            # Delete all records (order matters due to foreign keys)
            session.query(PaperField).delete()
            session.query(Paper).delete()
            session.query(Field).delete()

            session.commit()

            return {
                "papers_deleted": paper_count,
                "fields_deleted": field_count,
                "associations_deleted": paper_field_count,
            }
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def _extract_fields_from_subjects(self, subjects_str: str) -> list:
        """Extract field codes from subjects string."""
        if not subjects_str:
            return ["unknown"]

        fields = []
        # Split by comma and extract field codes
        for subject in subjects_str.split(","):
            subject = subject.strip()
            # Look for field code in parentheses
            if "(" in subject and ")" in subject:
                start = subject.find("(") + 1
                end = subject.find(")")
                field_code = subject[start:end].strip()
                # Clean up any trailing commas or other punctuation
                field_code = field_code.rstrip(",").strip()
                if field_code and field_code not in fields:
                    fields.append(field_code)
            else:
                fields.append(subject)

        # If no fields found, try to extract from the beginning
        if not fields:
            # Sometimes the field code is at the beginning
            parts = subjects_str.split()
            if parts and "." in parts[0]:
                field_code = parts[0].rstrip(",").strip()
                if field_code:
                    fields.append(field_code)
        return fields if fields else ["unknown"]

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        if not date_str:
            return None

        try:
            # Handle ISO format with timezone
            if date_str.endswith("Z"):
                date_str = date_str[:-1] + "+00:00"
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None
