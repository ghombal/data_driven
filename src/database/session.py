# src/database/session.py
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    async_sessionmaker, 
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.pool import NullPool
from sqlalchemy import text  # ADD THIS IMPORT
from contextlib import asynccontextmanager
import logging

from .config import settings
from .models.base import Base

logger = logging.getLogger(__name__)

class DatabaseSession:
    """Database session manager"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or self._build_database_url()
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        
    def _build_database_url(self) -> str:
        """Build database URL from configuration"""
        db_config = settings.database
        return (
            f"postgresql+asyncpg://{db_config.username}:{db_config.password}"
            f"@{db_config.host}:{db_config.port}/{db_config.database}"
        )
    
    async def init_engine(self) -> None:
        """Initialize database engine and session factory"""
        if self.engine is not None:
            return
            
        self.engine = create_async_engine(
            self.database_url,
            echo=settings.database.echo,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            pool_pre_ping=True,
            future=True
        )
        
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Database engine initialized")
    
    async def create_tables(self) -> None:
        """Create all database tables"""
        if self.engine is None:
            await self.init_engine()
            
        async with self.engine.begin() as conn:
            # Create schema first - WRAP IN text()
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS market_data"))
            
            # Create enums - WRAP IN text()
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE market_data.market_side AS ENUM ('bid', 'ask');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE market_data.tick_type AS ENUM ('last', 'bid', 'ask', 'midpoint');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE market_data.order_operation AS ENUM ('insert', 'update', 'delete');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created")
    
    async def create_hypertables(self) -> None:
        """Create TimescaleDB hypertables"""
        if self.engine is None:
            await self.init_engine()
            
        chunk_interval = settings.timescale.chunk_time_interval
        
        hypertable_queries = [
            f"SELECT create_hypertable('market_data.top_of_book', 'timestamp', "
            f"chunk_time_interval => INTERVAL '{chunk_interval}', if_not_exists => TRUE);",
            
            f"SELECT create_hypertable('market_data.tick_by_tick', 'timestamp', "
            f"chunk_time_interval => INTERVAL '{chunk_interval}', if_not_exists => TRUE);",
            
            f"SELECT create_hypertable('market_data.market_depth', 'timestamp', "
            f"chunk_time_interval => INTERVAL '{chunk_interval}', if_not_exists => TRUE);",
            
            f"SELECT create_hypertable('market_data.performance_metrics', 'timestamp', "
            f"chunk_time_interval => INTERVAL '{chunk_interval}', if_not_exists => TRUE);",
            
            f"SELECT create_hypertable('market_data.historical_bars', 'created_at', "
            f"chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);",
            
            f"SELECT create_hypertable('market_data.fundamental_data', 'timestamp', "
            f"chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);"
        ]
        
        async with self.engine.begin() as conn:
            for query in hypertable_queries:
                try:
                    await conn.execute(text(query))  # WRAP IN text()
                    logger.info(f"Created hypertable: {query}")
                except Exception as e:
                    logger.warning(f"Hypertable creation failed: {query} - {e}")
    
    async def setup_compression(self) -> None:
        """Setup compression policies"""
        if self.engine is None:
            await self.init_engine()
            
        compression_after = settings.timescale.compression_after
        
        compression_queries = [
            f"SELECT add_compression_policy('market_data.top_of_book', "
            f"INTERVAL '{compression_after}', if_not_exists => TRUE);",
            
            f"SELECT add_compression_policy('market_data.tick_by_tick', "
            f"INTERVAL '{compression_after}', if_not_exists => TRUE);",
            
            f"SELECT add_compression_policy('market_data.market_depth', "
            f"INTERVAL '{compression_after}', if_not_exists => TRUE);",
        ]
        
        async with self.engine.begin() as conn:
            for query in compression_queries:
                try:
                    await conn.execute(text(query))  # WRAP IN text()
                    logger.info(f"Added compression policy: {query}")
                except Exception as e:
                    logger.warning(f"Compression policy failed: {query} - {e}")
    
    async def close(self) -> None:
        """Close database engine"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None
            logger.info("Database engine closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager"""
        if self.session_factory is None:
            await self.init_engine()
        
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

# Global database session instance
db_session = DatabaseSession()

# Dependency for getting database session
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with db_session.get_session() as session:
        yield session