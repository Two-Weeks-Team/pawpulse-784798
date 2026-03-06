import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine

load_dotenv()

# ---------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost/pawpulse",
)

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True
)

Base = declarative_base()

# ---------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    pets = relationship("Pet", back_populates="owner")


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    breed = Column(String(100))
    age_years = Column(Integer)
    weight_kg = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="pets")
    logs = relationship("HealthLog", back_populates="pet")


class HealthLog(Base):
    __tablename__ = "health_logs"

    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)
    symptom_text = Column(Text, nullable=False)
    photo_url = Column(String(500))
    notes = Column(Text)

    pet = relationship("Pet", back_populates="logs")

# ---------------------------------------------------------------
# Helper utilities for FastAPI dependencies
# ---------------------------------------------------------------
def get_engine():
    """Expose the SQLAlchemy engine for migrations or startup tasks."""
    return engine

def get_session():
    """Create a new SQLAlchemy session. FastAPI will manage its lifecycle."""
    return SessionLocal()
