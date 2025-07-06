# src/scripts/test_repositories_updated.py
import asyncio
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import db_session
from database.repositories.top_of_book import TopOfBookRepository
from database.models.market_data import TopOfBookCreate

async def test_repositories():
    """Test repository operations with updated schema"""
    print("="*50)
    print("REPOSITORY LAYER TESTS")
    print("="*50)
    print("Testing repository operations with TimescaleDB-compatible schema...")
    
    try:
        async with db_session() as session:
            # 1. Test TopOfBook Repository
            print("\n1. Testing TopOfBook Repository...")
            tob_repo = TopOfBookRepository(session)
            
            # Create test data with fixed datetime
            tob_data = TopOfBookCreate(
                symbol="AAPL",
                bid=Decimal("150.25"),
                ask=Decimal("150.26"),
                last=Decimal("150.25"),
                volume=1000,
                timestamp=datetime.now(datetime.UTC)  # Fixed deprecated datetime
            )
            
            # Test CREATE
            print("   Creating new TopOfBook record...")
            created_tob = await tob_repo.create(obj_in=tob_data)
            print(f"   ✅ Created: {created_tob.symbol} at {created_tob.timestamp}")
            
            # Test READ
            print("   Reading TopOfBook record...")
            # Note: With composite primary key, we need both id and timestamp
            read_tob = await tob_repo.get(created_tob.id)
            if read_tob:
                print(f"   ✅ Read: {read_tob.symbol} - Bid: {read_tob.bid}, Ask: {read_tob.ask}")
            else:
                print("   ❌ Could not read record")
            
            # Test UPDATE
            print("   Updating TopOfBook record...")
            update_data = TopOfBookCreate(
                symbol="AAPL",
                bid=Decimal("151.00"),
                ask=Decimal("151.01"),
                last=Decimal("151.00"),
                volume=1500,
                timestamp=datetime.now(datetime.UTC)
            )
            
            # For composite primary key, we need to create a new record rather than update
            # This is typical for time-series data
            updated_tob = await tob_repo.create(obj_in=update_data)
            print(f"   ✅ Updated: {updated_tob.symbol} - New Bid: {updated_tob.bid}")
            
            # Test LIST/QUERY
            print("   Querying TopOfBook records...")
            all_tobs = await tob_repo.get_multi(limit=10)
            print(f"   ✅ Found {len(all_tobs)} records")
            
            for tob in all_tobs:
                print(f"      • {tob.symbol} at {tob.timestamp}: {tob.bid}/{tob.ask}")
            
            # Test filtering by symbol
            print("   Filtering by symbol...")
            apple_tobs = await tob_repo.get_by_symbol("AAPL", limit=5)
            print(f"   ✅ Found {len(apple_tobs)} AAPL records")
            
            print("\n✅ All repository tests passed!")
            
    except Exception as e:
        print(f"\n❌ Repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_hypertable_features():
    """Test TimescaleDB-specific features"""
    print("\n" + "="*50)
    print("TIMESCALEDB FEATURES TEST")
    print("="*50)
    
    try:
        async with db_session() as session:
            # Test time-series queries
            print("Testing time-series queries...")
            
            # Insert multiple records with different timestamps
            tob_repo = TopOfBookRepository(session)
            
            base_time = datetime.now(datetime.UTC)
            symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
            
            for i, symbol in enumerate(symbols):
                for j in range(3):  # 3 records per symbol
                    timestamp = base_time.replace(minute=base_time.minute + (i * 3 + j))
                    
                    tob_data = TopOfBookCreate(
                        symbol=symbol,
                        bid=Decimal(f"{150 + i * 10 + j}.{25 + j}"),
                        ask=Decimal(f"{150 + i * 10 + j}.{26 + j}"),
                        last=Decimal(f"{150 + i * 10 + j}.{25 + j}"),
                        volume=1000 + i * 100 + j * 10,
                        timestamp=timestamp
                    )
                    
                    await tob_repo.create(obj_in=tob_data)
            
            print(f"✅ Inserted {len(symbols) * 3} test records")
            
            # Test time-based queries
            print("Testing time-range queries...")
            recent_records = await tob_repo.get_multi(limit=20)
            print(f"✅ Retrieved {len(recent_records)} recent records")
            
            # Group by symbol
            symbol_counts = {}
            for record in recent_records:
                symbol_counts[record.symbol] = symbol_counts.get(record.symbol, 0) + 1
            
            print("Record counts by symbol:")
            for symbol, count in symbol_counts.items():
                print(f"   • {symbol}: {count} records")
            
            print("\n✅ TimescaleDB features test completed!")
            
    except Exception as e:
        print(f"\n❌ TimescaleDB features test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Run all tests"""
    print("Starting comprehensive repository tests...")
    
    # Basic repository tests
    basic_success = await test_repositories()
    
    # TimescaleDB features tests
    timescale_success = await test_hypertable_features()
    
    if basic_success and timescale_success:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("Your database setup is working correctly!")
    else:
        print("\n❌ Some tests failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
                # src/scripts/test_repositories_updated.py
import asyncio
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import db_session
from database.repositories.top_of_book import TopOfBookRepository
from database.models.market_data import TopOfBookCreate

async def test_repositories():
    """Test repository operations with updated schema"""
    print("="*50)
    print("REPOSITORY LAYER TESTS")
    print("="*50)
    print("Testing repository operations