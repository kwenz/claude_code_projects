"""Database migration script to handle schema changes."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import DatabaseManager
from models.base import Base
from models.paper import Paper
from models.field import Field
from models.paper_field import PaperField
import config


def migrate_database():
    """Migrate database to new schema with multiple fields support."""
    print("🔄 Starting database migration...")
    
    try:
        db = DatabaseManager(config.DATABASE_PATH)
        
        # Create all tables (this will create new ones, existing ones are preserved)
        Base.metadata.create_all(db.engine)
        print("✅ Database tables created/updated")
        
        # Initialize common fields
        initialize_fields(db)
        
        # Migrate existing papers to use the new field system
        migrate_existing_papers(db)
        
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True


def initialize_fields(db: DatabaseManager):
    """Initialize common arXiv fields."""
    print("📚 Initializing arXiv fields...")
    
    common_fields = [
        ('cs.AI', 'Artificial Intelligence'),
        ('cs.LG', 'Machine Learning'),
        ('cs.CL', 'Computation and Language'),
        ('cs.CV', 'Computer Vision and Pattern Recognition'),
        ('cs.RO', 'Robotics'),
        ('cs.NE', 'Neural and Evolutionary Computing'),
        ('hep-th', 'High Energy Physics - Theory'),
        ('hep-ph', 'High Energy Physics - Phenomenology'),
        ('math.ST', 'Statistics Theory'),
        ('stat.ML', 'Machine Learning (Statistics)'),
        ('q-bio.NC', 'Neurons and Cognition'),
        ('physics.data-an', 'Data Analysis, Statistics and Probability'),
    ]
    
    session = db.get_session()
    try:
        for code, name in common_fields:
            # Check if field already exists
            existing = session.query(Field).filter_by(code=code).first()
            if not existing:
                field = Field(code=code, name=name)
                session.add(field)
        
        session.commit()
        print(f"✅ Initialized {len(common_fields)} fields")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error initializing fields: {e}")
        raise e
    finally:
        session.close()


def migrate_existing_papers(db: DatabaseManager):
    """Migrate existing papers to use the new field system."""
    print("📄 Migrating existing papers...")
    
    session = db.get_session()
    try:
        # Get all papers that might have the old 'field' column
        papers = session.query(Paper).all()
        
        migrated_count = 0
        for paper in papers:
            # Check if paper already has field associations
            existing_associations = session.query(PaperField).filter_by(paper_id=paper.arxiv_id).count()
            
            if existing_associations == 0:
                # Extract fields from subjects string
                fields = extract_fields_from_subjects(paper.subjects)
                
                # Create field associations
                for i, field_code in enumerate(fields):
                    # Ensure field exists
                    field = session.query(Field).filter_by(code=field_code).first()
                    if not field:
                        # Create field if it doesn't exist
                        field = Field(code=field_code, name=field_code)
                        session.add(field)
                        session.flush()  # Flush to get the field in the session
                    
                    # Create association
                    association = PaperField(
                        paper_id=paper.arxiv_id,
                        field_code=field_code,
                        is_primary=(i == 0)  # First field is primary
                    )
                    session.add(association)
                
                migrated_count += 1
        
        session.commit()
        print(f"✅ Migrated {migrated_count} papers to new field system")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error migrating papers: {e}")
        raise e
    finally:
        session.close()


def extract_fields_from_subjects(subjects_str: str) -> list:
    """Extract field codes from subjects string."""
    if not subjects_str:
        return ['unknown']
    
    fields = []
    # Split by comma and extract field codes
    for subject in subjects_str.split(','):
        subject = subject.strip()
        # Look for field code in parentheses
        if '(' in subject and ')' in subject:
            start = subject.find('(') + 1
            end = subject.find(')')
            field_code = subject[start:end].strip()
            if field_code and field_code not in fields:
                fields.append(field_code)
    
    # If no fields found, try to extract from the beginning
    if not fields:
        # Sometimes the field code is at the beginning
        parts = subjects_str.split()
        if parts and '.' in parts[0]:
            fields.append(parts[0])
    
    return fields if fields else ['unknown']


if __name__ == "__main__":
    migrate_database()
