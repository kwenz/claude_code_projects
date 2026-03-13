"""Base model configuration for all database models."""

from sqlalchemy.ext.declarative import declarative_base

# Single Base instance for all models
Base = declarative_base()
