"""
Database configuration and models.

Handles SQLAlchemy setup and defines all database models.
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import uuid
import os

from app.core.config import settings

# Determine database URL
# Use provided URL first; otherwise default to local SQLite for MVP
db_url = settings.DATABASE_URL or "sqlite:///./analytics.db"

# Create database engine
engine = create_engine(
    db_url,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


# ============================================================================
# Database Models
# ============================================================================


class Dataset(Base):
    """Dataset model representing uploaded files."""

    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    rows = Column(Integer, nullable=False)
    columns = Column(Integer, nullable=False)
    column_info = Column(JSON, nullable=True)  # Store column types and metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Dataset {self.id}: {self.filename}>"


class Dashboard(Base):
    """Dashboard model storing processed dashboard data."""

    __tablename__ = "dashboards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False, index=True)
    summary = Column(JSON, nullable=False)  # KPIs and dataset summary
    charts = Column(JSON, nullable=False)  # Recommended charts with data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Dashboard {self.id}: {self.dataset_id}>"


class ChatSession(Base):
    """Chat session model for dataset-specific conversations."""

    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ChatSession {self.id}: {self.dataset_id}>"


class ChatMessage(Base):
    """Chat message model storing conversation history."""

    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ChatMessage {self.id}: {self.role}>"


# ============================================================================
# Database Functions
# ============================================================================


def get_db() -> Session:
    """
    Get database session dependency.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)
