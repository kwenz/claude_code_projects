"""Association table for paper-field many-to-many relationship."""

from sqlalchemy import Column, String, ForeignKey, Boolean
from .base import Base


class PaperField(Base):
    """Association table for paper-field many-to-many relationship."""
    __tablename__ = 'paper_fields'
    
    # Composite primary key
    paper_id = Column(String(50), ForeignKey('papers.arxiv_id'), primary_key=True)
    field_code = Column(String(20), ForeignKey('fields.code'), primary_key=True)
    
    # Additional attributes
    is_primary = Column(Boolean, default=False)  # Mark the primary field
    
    def __repr__(self):
        return f"<PaperField(paper_id='{self.paper_id}', field_code='{self.field_code}', primary={self.is_primary})>"
