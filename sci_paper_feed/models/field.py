"""Field model for arXiv categories."""

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from .base import Base


class Field(Base):
    """Field model for storing arXiv categories."""
    __tablename__ = 'fields'
    
    # Primary key
    code = Column(String(20), primary_key=True)  # e.g., 'cs.AI', 'hep-th'
    
    # Field metadata
    name = Column(String(200), nullable=False)  # e.g., 'Artificial Intelligence'
    description = Column(Text)  # Optional description
    
    # Relationships
    papers = relationship("Paper", secondary="paper_fields", back_populates="fields")
    
    def __repr__(self):
        return f"<Field(code='{self.code}', name='{self.name}')>"
