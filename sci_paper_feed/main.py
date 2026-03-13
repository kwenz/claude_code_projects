"""Main entry point for the AI Research Paper Feed application."""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_web_app():
    """Run the web application."""
    from scripts.run_app import main
    main()

def init_database():
    """Initialize the database."""
    from scripts.init_db import main
    main()

def setup_llm():
    """Setup LLM configuration."""
    from utils.setup_free_llm import main
    main()

def purge_database():
    """Purge all data from the database."""
    from services.paper_service import PaperService
    import config
    
    # Confirmation prompt
    print("⚠️  WARNING: This will permanently delete ALL papers, fields, and analysis data from the database!")
    print("This action cannot be undone.")
    confirmation = input("Are you sure you want to proceed? Type 'YES' to confirm: ")
    
    if confirmation != 'YES':
        print("Database purge cancelled.")
        return
    
    paper_service = PaperService(db_path=config.DATABASE_PATH)
    try:
        result = paper_service.purge_database()
        print("✅ Database purged successfully!")
        print(f"Deleted:")
        print(f"  - {result['papers_deleted']} papers")
        print(f"  - {result['fields_deleted']} fields")
        print(f"  - {result['associations_deleted']} field associations")
    except Exception as e:
        print(f"❌ Error purging database: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Research Paper Feed")
    parser.add_argument("command", choices=["web", "init-db", "setup-llm", "purge"], 
                       help="Command to run")
    
    args = parser.parse_args()
    
    if args.command == "web":
        run_web_app()
    elif args.command == "init-db":
        init_database()
    elif args.command == "setup-llm":
        setup_llm()
    elif args.command == "purge":
        purge_database()