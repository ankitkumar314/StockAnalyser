from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Manages PostgreSQL database connection and session lifecycle.
    Uses connection pooling for efficient resource management.
    """
    
    _engine = None
    _session_factory = None
    _scoped_session = None
    
    @classmethod
    def initialize(cls):
        """
        Initialize database engine and session factory.
        Should be called once at application startup.
        """
        try:
            if cls._engine is not None:
                logger.warning("Database already initialized")
                return
            
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                logger.warning("DATABASE_URL not set. Database features disabled.")
                return
            
            pool_size = int(os.getenv("DATABASE_POOL_SIZE", "5"))
            max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
            echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"
            
            cls._engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,
                echo=echo
            )
            
            cls._session_factory = sessionmaker(
                bind=cls._engine,
                autocommit=False,
                autoflush=False
            )
            
            cls._scoped_session = scoped_session(cls._session_factory)
            
            logger.info(f"Database initialized successfully (pool_size={pool_size}, max_overflow={max_overflow})")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    @classmethod
    def get_engine(cls):
        """Get the database engine."""
        if cls._engine is None:
            cls.initialize()
        return cls._engine
    
    @classmethod
    def get_session(cls):
        """
        Get a new database session.
        Caller is responsible for closing the session.
        
        Usage:
            session = DatabaseConnection.get_session()
            try:
                # Use session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        """
        if cls._session_factory is None:
            cls.initialize()
        
        if cls._session_factory is None:
            return None
        
        return cls._session_factory()
    
    @classmethod
    def get_scoped_session(cls):
        """
        Get a thread-local scoped session.
        Automatically manages session lifecycle per thread.
        """
        if cls._scoped_session is None:
            cls.initialize()
        return cls._scoped_session
    
    @classmethod
    def close_all(cls):
        """
        Close all database connections.
        Should be called at application shutdown.
        """
        try:
            if cls._scoped_session:
                cls._scoped_session.remove()
            
            if cls._engine:
                cls._engine.dispose()
                logger.info("Database connections closed")
            
            cls._engine = None
            cls._session_factory = None
            cls._scoped_session = None
            
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}")
    
    @classmethod
    def is_enabled(cls):
        """Check if database is configured and enabled."""
        return os.getenv("DATABASE_URL") is not None
    
    @classmethod
    def create_tables(cls):
        """
        Create all tables in the database.
        Should only be used for development/testing.
        Use Alembic migrations for production.
        """
        try:
            from app.database.models import Base
            
            if cls._engine is None:
                cls.initialize()
            
            if cls._engine is None:
                logger.warning("Cannot create tables: database not initialized")
                return
            
            Base.metadata.create_all(cls._engine)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise


def get_db():
    """
    Dependency injection for FastAPI routes.
    Provides a database session that is automatically closed after request.
    
    Usage in FastAPI:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = DatabaseConnection.get_session()
    if db is None:
        return None
    
    try:
        yield db
    finally:
        db.close()
