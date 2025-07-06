# src/scripts/setup_database.py
import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database. import db_session
from database.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def setup_database():
    """Setup database with tables and hypertables"""
    try:
        logger.info("Starting database setup...")
        
        # Initialize database engine
        await db_session.init_engine()
        logger.info("Database engine initialized")
        
        # Create tables
        await db_session.create_tables()
        logger.info("Database tables created")
        
        # Create hypertables
        await db_session.create_hypertables()
        logger.info("TimescaleDB hypertables created")
        
        # Setup compression
        await db_session.setup_compression()
        logger.info("Compression policies configured")
        
        logger.info("Database setup completed successfully!")
        
        # Print configuration summary
        print("\n" + "="*50)
        print("DATABASE CONFIGURATION SUMMARY")
        print("="*50)
        print(f"Database: {settings.database.database}")
        print(f"Host: {settings.database.host}:{settings.database.port}")
        print(f"Pool Size: {settings.database.pool_size}")
        print(f"Chunk Interval: {settings.timescale.chunk_time_interval}")
        print(f"Compression After: {settings.timescale.compression_after}")
        print(f"Retention Policy: {settings.timescale.retention_policy}")
        print(f"Symbols: {', '.join(settings.symbols.development)}")
        print(f"Batch Size: {settings.symbols.batch_size}")
        print(f"Flush Interval: {settings.symbols.flush_interval}s")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise
    finally:
        await db_session.close()

if __name__ == "__main__":
    asyncio.run(setup_database())