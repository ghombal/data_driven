# src/scripts/diagnose_database.py
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import db_session
from database.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose_database():
    """Diagnose database state"""
    try:
        await db_session.init_engine()
        logger.info("Database engine initialized successfully")
        
        async with db_session.get_session() as session:
            # Check if schema exists
            schema_check = await session.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'market_data'
            """)
            schema_exists = schema_check.scalar()
            
            if schema_exists:
                print("✅ Schema 'market_data' exists")
            else:
                print("❌ Schema 'market_data' does not exist")
                return False
            
            # Check if tables exist
            tables_check = await session.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'market_data'
                ORDER BY table_name
            """)
            tables = [row[0] for row in tables_check.fetchall()]
            
            if tables:
                print(f"✅ Found {len(tables)} tables in market_data schema:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("❌ No tables found in market_data schema")
                return False
            
            # Check if TimescaleDB extension is enabled
            extension_check = await session.execute("""
                SELECT extname 
                FROM pg_extension 
                WHERE extname = 'timescaledb'
            """)
            extension_exists = extension_check.scalar()
            
            if extension_exists:
                print("✅ TimescaleDB extension is enabled")
            else:
                print("❌ TimescaleDB extension is not enabled")
                return False
            
            # Check if hypertables exist
            hypertable_check = await session.execute("""
                SELECT hypertable_name 
                FROM timescaledb_information.hypertables 
                WHERE hypertable_schema = 'market_data'
            """)
            hypertables = [row[0] for row in hypertable_check.fetchall()]
            
            if hypertables:
                print(f"✅ Found {len(hypertables)} hypertables:")
                for hypertable in hypertables:
                    print(f"   - {hypertable}")
            else:
                print("❌ No hypertables found")
                return False
                
            print("\n✅ Database is properly configured!")
            return True
            
    except Exception as e:
        print(f"❌ Database diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db_session.close()

async def main():
    """Run database diagnosis"""
    print("="*50)
    print("DATABASE DIAGNOSIS")
    print("="*50)
    
    success = await diagnose_database()
    
    if not success:
        print("\n🔧 Database needs setup. Run: python src/scripts/setup_database_fixed.py")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)