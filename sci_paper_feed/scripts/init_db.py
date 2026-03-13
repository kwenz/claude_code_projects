"""Initialize the database for the paper feed application."""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import DatabaseManager

from models.base import Base
from models.paper import Paper
from models.field import Field
from models.paper_field import PaperField
import config


def main():
    """Initialize the database."""
    print("🗄️ Initializing database...")

    try:
        # Create database manager (this will create tables if they don't exist)
        db = DatabaseManager(config.DATABASE_PATH)

        print(f"✅ Database initialized successfully at: {config.DATABASE_PATH}")
        print("📊 Tables created:")
        print("  - papers: Store analyzed research papers")

        # Show some basic info
        session = db.get_session()
        try:
            from models.paper import Paper

            paper_count = session.query(Paper).count()
            print(f"📄 Current papers in database: {paper_count}")

            if paper_count > 0:
                analyzed_count = (
                    session.query(Paper).filter(Paper.analyzed == True).count()
                )
                print(f"🤖 Analyzed papers: {analyzed_count}")

            # Show available fields
            fields = session.query(Field.code).all()
            if fields:
                field_list = [f[0] for f in fields]
                print(f"📚 Available fields: {', '.join(field_list)}")
        finally:
            session.close()

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

    return True


if __name__ == "__main__":
    main()
