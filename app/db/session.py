"""
Database session management and connection.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://aivision:password@localhost:5432/aivision"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=os.getenv("DEBUG", "False").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session.
    Use with FastAPI Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from app.db.models import Base
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all database tables (use with caution!)"""
    from app.db.models import Base
    Base.metadata.drop_all(bind=engine)
