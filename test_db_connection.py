"""
Test database connection script
Save this as test_db_connection.py in your project root
"""

import asyncio
import asyncpg
from src.database.session import db_session

async def test_connection():
    """Test database connection using your app's configuration"""
    
    print("Testing database connection...")
    print("=" * 50)
    
    # Method 1: Test with your app's session
    try:
        print("1. Testing with your app's db_session...")
        
        # This will show us what URL is being built
        url = db_session._build_database_url()
        print(f"   Database URL: {url}")
        
        # Test connection
        await db_session.create_tables()
        print("   ✅ Connection successful!")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    # Method 2: Test with direct connection
    try:
        print("\n2. Testing direct connection...")
        conn = await asyncpg.connect(
            user="market_user",
            password="Prince@2",
            database="market_data_db", 
            host="localhost",
            port=5432
        )
        print("   ✅ Direct connection successful!")
        await conn.close()
        
    except Exception as e:
        print(f"   ❌ Direct connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    # Method 3: Test configuration loading
    try:
        print("\n3. Testing configuration loading...")
        from src.config import settings  # Adjust import path as needed
        
        db_config = settings.database
        print(f"   Username: {db_config.username}")
        print(f"   Database: {db_config.database}")
        print(f"   Host: {db_config.host}")
        print(f"   Port: {db_config.port}")
        print(f"   Password: {'*' * len(db_config.password)}")
        
    except Exception as e:
        print(f"   ❌ Configuration loading failed: {e}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_connection())
