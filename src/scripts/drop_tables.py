# src/scripts/drop_tables.py
import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.config import settings
import asyncpg

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def drop_tables():
    """Drop all tables to start fresh"""
    try:
        # Connect directly with asyncpg
        db_config = settings.database
        connection = await asyncpg.connect(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.username,
            password=db_config.password
        )
        
        logger.info("Connected to database successfully")
        
        print("="*50)
        print("DROPPING EXISTING TABLES")
        print("="*50)
        
        # Drop tables in reverse order to handle dependencies
        tables_to_drop = [
            'market_data.performance_metrics',
            'market_data.fundamental_data',
            'market_data.historical_bars',
            'market_data.market_depth',
            'market_data.tick_by_tick',
            'market_data.top_of_book'
        ]
        
        for table in tables_to_drop:
            try:
                await connection.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                logger.info(f"✅ Dropped table: {table}")
            except Exception as e:
                logger.warning(f"⚠️  Could not drop {table}: {e}")
        
        await connection.close()
        
        print("\n✅ All tables dropped successfully!")
        print("Now run: python src/scripts/setup_database_fixed.py")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(drop_tables())
    sys.exit(0 if success else 1)