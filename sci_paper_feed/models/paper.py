"""Paper model for the database."""

from sqlalchemy import Column, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base


class Paper(Base):
    """Paper model for storing analyzed research papers."""
    __tablename__ = 'papers'
    
    # Primary key
    arxiv_id = Column(String(50), primary_key=True)
    
    # Paper metadata
    title = Column(Text, nullable=False)
    authors = Column(Text, nullable=False)
    abstract = Column(Text, nullable=False)
    arxiv_url = Column(String(200), nullable=False)
    
    # arXiv categorization
    subjects = Column(Text)  # Full subject list from arXiv
    
    # Relationships
    fields = relationship("Field", secondary="paper_fields", back_populates="papers")
    
    # Dates
    date_announced = Column(DateTime, nullable=False, index=True)  # When appeared on arXiv
    date_submitted = Column(DateTime)  # Original submission date
    date_added = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)  # When added to our DB
    
    # AI Analysis results
    ai_score = Column(Float)  # 1-10 score from LLM
    ai_explanation = Column(Text)  # Why it's interesting
    ai_key_insights = Column(Text)  # Key insights
    analyzed = Column(Boolean, default=False, index=True)  # Whether it's been analyzed
    analysis_type = Column(String(20))  # "llm" or "fallback"
    
    def __repr__(self):
        return f"<Paper(arxiv_id='{self.arxiv_id}', title='{self.title[:50]}...', score={self.ai_score})>"
