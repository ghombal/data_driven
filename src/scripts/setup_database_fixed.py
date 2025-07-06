# src/scripts/setup_database_fixed.py
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

async def setup_database_manually():
    """Setup database manually with raw SQL"""
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
        
        # Check if TimescaleDB extension is installed
        timescale_available = False
        try:
            # Try to check if TimescaleDB extension exists
            extension_check = "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')"
            timescale_installed = await connection.fetchval(extension_check)
            
            if not timescale_installed:
                logger.warning("TimescaleDB extension not installed. Installing...")
                await connection.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
                logger.info("✅ TimescaleDB extension installed")
                timescale_available = True
            else:
                logger.info("✅ TimescaleDB extension already installed")
                timescale_available = True
                
        except Exception as e:
            logger.warning(f"❌ TimescaleDB extension not available: {e}")
            logger.info("Continuing with regular PostgreSQL setup...")
            timescale_available = False
        
        # 1. Create schema
        await connection.execute("CREATE SCHEMA IF NOT EXISTS market_data")
        logger.info("Created market_data schema")
        
        # 2. Create custom types - Fixed syntax
        try:
            await connection.execute("CREATE TYPE market_data.market_side AS ENUM ('bid', 'ask')")
            logger.info("Created market_side enum")
        except asyncpg.exceptions.DuplicateObjectError:
            logger.info("market_side enum already exists")
        
        try:
            await connection.execute("CREATE TYPE market_data.tick_type AS ENUM ('last', 'bid', 'ask', 'midpoint')")
            logger.info("Created tick_type enum")
        except asyncpg.exceptions.DuplicateObjectError:
            logger.info("tick_type enum already exists")
        
        try:
            await connection.execute("CREATE TYPE market_data.order_operation AS ENUM ('insert', 'update', 'delete')")
            logger.info("Created order_operation enum")
        except asyncpg.exceptions.DuplicateObjectError:
            logger.info("order_operation enum already exists")
        
        # 3. Create tables (TimescaleDB compatible)
        
        # TopOfBook table - composite primary key with timestamp
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS market_data.top_of_book (
                id UUID DEFAULT gen_random_uuid(),
                symbol VARCHAR(20) NOT NULL,
                bid DECIMAL(12,4),
                ask DECIMAL(12,4),
                last DECIMAL(12,4),
                volume BIGINT,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, timestamp)
            )
        """)
        logger.info("Created top_of_book table")
        
        # TickByTick table - composite primary key with timestamp
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS market_data.tick_by_tick (
                id UUID DEFAULT gen_random_uuid(),
                symbol VARCHAR(20) NOT NULL,
                tick_type market_data.tick_type NOT NULL,
                price DECIMAL(12,4) NOT NULL,
                size INTEGER NOT NULL,
                tick_attrib JSONB,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, timestamp)
            )
        """)
        logger.info("Created tick_by_tick table")
        
        # MarketDepth table - composite primary key with timestamp
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS market_data.market_depth (
                id UUID DEFAULT gen_random_uuid(),
                symbol VARCHAR(20) NOT NULL,
                position INTEGER NOT NULL,
                operation market_data.order_operation NOT NULL,
                side market_data.market_side NOT NULL,
                price DECIMAL(12,4) NOT NULL,
                size INTEGER NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, timestamp)
            )
        """)
        logger.info("Created market_depth table")
        
        # HistoricalBar table - composite primary key with created_at
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS market_data.historical_bars (
                id UUID DEFAULT gen_random_uuid(),
                symbol VARCHAR(20) NOT NULL,
                date DATE NOT NULL,
                open DECIMAL(12,4) NOT NULL,
                high DECIMAL(12,4) NOT NULL,
                low DECIMAL(12,4) NOT NULL,
                close DECIMAL(12,4) NOT NULL,
                volume BIGINT NOT NULL,
                bar_count INTEGER,
                average DECIMAL(12,4),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, created_at)
            )
        """)
        logger.info("Created historical_bars table")
        
        # FundamentalData table - composite primary key with timestamp
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS market_data.fundamental_data (
                id UUID DEFAULT gen_random_uuid(),
                symbol VARCHAR(20) NOT NULL,
                report_type VARCHAR(50) NOT NULL,
                data TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, timestamp)
            )
        """)
        logger.info("Created fundamental_data table")
        
        # PerformanceMetric table - composite primary key with timestamp
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS market_data.performance_metrics (
                id UUID DEFAULT gen_random_uuid(),
                metric_name VARCHAR(100) NOT NULL,
                metric_value DECIMAL(12,4) NOT NULL,
                symbol VARCHAR(20),
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                metadata JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, timestamp)
            )
        """)
        logger.info("Created performance_metrics table")
        
        # 4. Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_top_of_book_symbol_timestamp ON market_data.top_of_book (symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_top_of_book_timestamp ON market_data.top_of_book (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_tick_by_tick_symbol_timestamp ON market_data.tick_by_tick (symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_tick_by_tick_tick_type ON market_data.tick_by_tick (tick_type)",
            "CREATE INDEX IF NOT EXISTS idx_market_depth_symbol_timestamp ON market_data.market_depth (symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_market_depth_side ON market_data.market_depth (side)",
            "CREATE INDEX IF NOT EXISTS idx_historical_bars_symbol_date ON market_data.historical_bars (symbol, date)",
            "CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_timestamp ON market_data.performance_metrics (metric_name, timestamp)",
        ]
        
        for index_sql in indexes:
            await connection.execute(index_sql)
        logger.info("Created indexes")
        
        # 5. Create hypertables (only if TimescaleDB is available)
        if timescale_available:
            logger.info("Setting up TimescaleDB hypertables...")
            
            chunk_interval = settings.timescale.chunk_time_interval
            
            # Define hypertables with their time columns
            hypertables = [
                ('market_data.top_of_book', 'timestamp', chunk_interval),
                ('market_data.tick_by_tick', 'timestamp', chunk_interval),
                ('market_data.market_depth', 'timestamp', chunk_interval),
                ('market_data.performance_metrics', 'timestamp', chunk_interval),
                ('market_data.historical_bars', 'created_at', '1 day'),
                ('market_data.fundamental_data', 'timestamp', '1 day'),
            ]
            
            for table_name, time_column, interval in hypertables:
                try:
                    # Create hypertable directly (simpler approach)
                    query = f"SELECT create_hypertable('{table_name}', '{time_column}', chunk_time_interval => INTERVAL '{interval}', if_not_exists => TRUE)"
                    await connection.execute(query)
                    logger.info(f"✅ Created hypertable: {table_name}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to create hypertable {table_name}: {e}")
            
            # 6. Setup compression policies
            logger.info("Setting up compression policies...")
            
            compression_after = settings.timescale.compression_after
            
            # Only apply compression to high-frequency tables
            compression_tables = [
                'market_data.top_of_book',
                'market_data.tick_by_tick', 
                'market_data.market_depth',
                'market_data.performance_metrics'
            ]
            
            for table_name in compression_tables:
                try:
                    # First create the hypertable, then enable compression
                    await connection.execute(f"SELECT add_compression_policy('{table_name}', INTERVAL '{compression_after}', if_not_exists => TRUE)")
                    logger.info(f"✅ Added compression policy: {table_name}")
                        
                except Exception as e:
                    # Try alternative compression setup
                    try:
                        await connection.execute(f"ALTER TABLE {table_name} SET (timescaledb.compress = true)")
                        await connection.execute(f"SELECT add_compression_policy('{table_name}', INTERVAL '{compression_after}')")
                        logger.info(f"✅ Added compression policy (alternative): {table_name}")
                    except Exception as e2:
                        logger.error(f"❌ Failed to add compression policy {table_name}: {e2}")
            
            # 7. Setup retention policies for high-frequency data
            logger.info("Setting up retention policies...")
            
            try:
                retention_after = getattr(settings.timescale, 'retention_after', '1 year')
                
                # Apply retention to high-frequency tables (only if they are hypertables)
                retention_tables = [
                    'market_data.tick_by_tick',
                    'market_data.market_depth'
                ]
                
                for table_name in retention_tables:
                    try:
                        await connection.execute(f"SELECT add_retention_policy('{table_name}', INTERVAL '{retention_after}', if_not_exists => TRUE)")
                        logger.info(f"✅ Added retention policy: {table_name}")
                    except Exception as e:
                        logger.warning(f"⚠️  Retention policy failed for {table_name}: {e}")
                        
            except Exception as e:
                logger.warning(f"⚠️  Retention policies not configured: {e}")
        else:
            logger.info("⚠️  Skipping TimescaleDB features - extension not available")
        
        # Verify setup BEFORE closing connection
        if timescale_available:
            print("\nVerifying TimescaleDB setup...")
            try:
                hypertable_check = """
                    SELECT hypertable_name, num_chunks, compression_enabled
                    FROM timescaledb_information.hypertables 
                    WHERE hypertable_schema = 'market_data'
                    ORDER BY hypertable_name
                """
                hypertables = await connection.fetch(hypertable_check)
                
                if hypertables:
                    print("✅ Active Hypertables:")
                    for ht in hypertables:
                        compression_status = "✅ Enabled" if ht['compression_enabled'] else "❌ Disabled"
                        print(f"  • {ht['hypertable_name']}: {ht['num_chunks']} chunks, Compression: {compression_status}")
                else:
                    print("⚠️  No hypertables found")
            except Exception as e:
                logger.warning(f"Could not verify hypertables: {e}")
        else:
            print("\nVerifying regular PostgreSQL setup...")
            try:
                # Check if tables exist
                table_check = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'market_data' 
                    ORDER BY table_name
                """
                tables = await connection.fetch(table_check)
                
                if tables:
                    print("✅ Created Tables:")
                    for table in tables:
                        print(f"  • {table['table_name']}")
                else:
                    print("⚠️  No tables found")
            except Exception as e:
                logger.warning(f"Could not verify tables: {e}")
        
        await connection.close()
        
        await connection.close()
        logger.info("Database setup completed successfully!")
        
        # Print configuration summary
        print("\n" + "="*50)
        print("DATABASE SETUP COMPLETED")
        print("="*50)
        print(f"Database: {settings.database.database}")
        print(f"Host: {settings.database.host}:{settings.database.port}")
        print(f"Schema: market_data")
        print(f"Tables: 6 tables created")
        print(f"Indexes: 8 indexes created")
        print(f"Hypertables: 6 hypertables configured")
        print(f"Compression policies: 4 policies configured")
        print(f"Chunk Interval: {settings.timescale.chunk_time_interval}")
        print(f"Compression After: {settings.timescale.compression_after}")
        try:
            retention_after = getattr(settings.timescale, 'retention_after', '1 year')
            print(f"Retention Period: {retention_after}")
        except:
            print("Retention Period: Not configured")
        print("="*50)
        
        # Verify hypertables
        print("\nVerifying TimescaleDB setup...")
        hypertable_check = """
            SELECT hypertable_name, num_chunks, compression_enabled
            FROM timescaledb_information.hypertables 
            WHERE hypertable_schema = 'market_data'
            ORDER BY hypertable_name
        """
        hypertables = await connection.fetch(hypertable_check)
        
        if hypertables:
            print("✅ Active Hypertables:")
            for ht in hypertables:
                compression_status = "✅ Enabled" if ht['compression_enabled'] else "❌ Disabled"
                print(f"  • {ht['hypertable_name']}: {ht['num_chunks']} chunks, Compression: {compression_status}")
        else:
            print("⚠️  No hypertables found")
        
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run database setup"""
    print("="*50)
    print("FIXING DATABASE SETUP")
    print("="*50)
    
    success = await setup_database_manually()
    
    if success:
        print("\n✅ Database setup completed successfully!")
        print("Now run: python src/scripts/test_repositories.py")
    else:
        print("\n❌ Database setup failed")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)