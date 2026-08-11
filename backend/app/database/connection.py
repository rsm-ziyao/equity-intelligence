"""Database connection management and session factory."""

import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from .models import Base


def get_database_url() -> str:
    """Get database URL from environment or construct from components."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    
    # Fall back to component-based construction
    user = os.getenv("POSTGRES_USER", "equityuser")
    password = os.getenv("POSTGRES_PASSWORD", "equitypass")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "equitydb")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


_engine = None
_SessionLocal = None


def get_engine():
    """Get or create SQLAlchemy engine (singleton)."""
    global _engine
    if _engine is None:
        db_url = get_database_url()
        _engine = create_engine(
            db_url,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            pool_pre_ping=True,  # Test connections before using
        )
    return _engine


def get_session_factory():
    """Get or create session factory (singleton)."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )
    return _SessionLocal


def get_session() -> Generator[Session, None, None]:
    """Dependency for FastAPI and testing. Yields a database session."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Initialize database: create all tables.
    
    Safe to call multiple times; idempotent via SQLAlchemy.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """Check if database is reachable. Raises on failure."""
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        raise RuntimeError(f"Database connection failed: {e}") from e
