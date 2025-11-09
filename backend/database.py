"""
Database models and setup for MedLearn platform.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

# Database setup
DATABASE_URL = "sqlite:///./medlearn.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """User model for authentication and tracking."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship("TrainingSession", back_populates="user")


class TrainingSession(Base):
    """Training session model to store surgery simulation data."""
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Session data
    procedure = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration = Column(String(50))  # e.g., "24 min 30 sec"
    final_score = Column(Integer, default=0)
    failed = Column(Boolean, default=False)
    complications = Column(Integer, default=0)
    interactions = Column(Integer, default=0)
    phases_completed = Column(Integer, default=0)

    # Timeline stored as JSON
    timeline_json = Column(Text)  # JSON string of timeline events

    # Relationships
    user = relationship("User", back_populates="sessions")

    @property
    def timeline(self):
        """Parse timeline from JSON."""
        if self.timeline_json:
            return json.loads(self.timeline_json)
        return []

    @timeline.setter
    def timeline(self, value):
        """Store timeline as JSON."""
        self.timeline_json = json.dumps(value)


# Create tables
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
