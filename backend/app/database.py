"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create database engine
# Support both psycopg2 and psycopg3
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    # For psycopg3, use postgresql+psycopg://
    # For psycopg2, keep postgresql://
    # Auto-detect based on installed package
    try:
        import psycopg  # psycopg3
        if not database_url.startswith("postgresql+psycopg://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://")
    except ImportError:
        pass  # Use default (psycopg2)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for getting database session
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
