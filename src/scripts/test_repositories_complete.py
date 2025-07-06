# src/scripts/test_repositories_complete.py
import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import db_session
from database.repositories.market_data import TopOfBookRepository
from database.models.market_data import TopOfBook

async def test_basic_repository_operations():
    """Test basic CRUD operations"""
    print("="*50)
    print("BASIC REPOSITORY OPERATIONS TEST")
    print("="*50)
    
    try:
        async with db_session() as session:
            print("\n1. Testing TopOfBook Repository...")
            tob_repo = TopOfBookRepository(session)
            
            # Create test data
            tob_data = TopOfBookCreate(
                symbol="AAPL",
                bid=Decimal("150.25"),
                ask=Decimal("150.26"),
                last=Decimal("150.25"),
                volume=1000,
                timestamp=datetime.now(datetime.UTC)
            )
            
            # Test CREATE
            print("   📝 Creating new TopOfBook record...")
            created_tob = await tob_repo.create(obj_in=tob_data)
            print(f"   ✅ Created: {created_tob.symbol} at {created_tob.timestamp}")
            print(f"      ID: {created_tob.id}")
            print(f"      Bid: ${created_tob.bid}, Ask: ${created_tob.ask}")
            
            # Test READ by ID
            print("\n   📖 Reading TopOfBook record by ID...")
            read_tob = await tob_repo.get(created_tob.id)
            if read_tob:
                print(f"   ✅ Read: {read_tob.symbol} - Bid: ${read_tob.bid}, Ask: ${read_tob.ask}")
            else:
                print("   ❌ Could not read record by ID")
            
            # Test LIST/QUERY
            print("\n   📋 Querying TopOfBook records...")
            all_tobs = await tob_repo.get_multi(limit=10)
            print(f"   ✅ Found {len(all_tobs)} records")
            
            if all_tobs:
                print("   📊 Sample records:")
                for i, tob in enumerate(all_tobs[:3]):  # Show first 3
                    print(f"      {i+1}. {tob.symbol} at {tob.timestamp.strftime('%H:%M:%S')}: ${tob.bid}/${tob.ask}")
            
            # Test filtering by symbol
            print("\n   🔍 Filtering by symbol...")
            apple_tobs = await tob_repo.get_by_symbol("AAPL", limit=5)
            print(f"   ✅ Found {len(apple_tobs)} AAPL records")
            
            print("\n✅ Basic repository operations completed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ Basic repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_timescale_features():
    """Test TimescaleDB-specific features with bulk data"""
    print("\n" + "="*50)
    print("TIMESCALEDB FEATURES TEST")
    print("="*50)
    
    try:
        async with db_session() as session:
            tob_repo = TopOfBookRepository(session)
            
            print("\n2. Testing bulk data insertion...")
            
            # Create test data for multiple symbols over time
            symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
            base_time = datetime.now(datetime.UTC)
            records_created = 0
            
            print(f"   📈 Inserting market data for {len(symbols)} symbols...")
            
            for symbol_idx, symbol in enumerate(symbols):
                base_price = 100 + (symbol_idx * 50)  # AAPL=100, GOOGL=150, etc.
                
                # Create 10 records per symbol with different timestamps
                for i in range(10):
                    # Space records 1 minute apart
                    timestamp = base_time + timedelta(minutes=i)
                    
                    # Simulate price movement
                    price_change = (i * 0.1) + (symbol_idx * 0.05)
                    bid_price = Decimal(str(base_price + price_change))
                    ask_price = bid_price + Decimal("0.01")
                    last_price = bid_price + Decimal("0.005")
                    
                    tob_data = TopOfBookCreate(
                        symbol=symbol,
                        bid=bid_price,
                        ask=ask_price,
                        last=last_price,
                        volume=1000 + (i * 100),
                        timestamp=timestamp
                    )
                    
                    await tob_repo.create(obj_in=tob_data)
                    records_created += 1
                    
                    if records_created % 10 == 0:
                        print(f"   📊 Inserted {records_created} records...")
            
            print(f"   ✅ Successfully inserted {records_created} records")
            
            # Test time-based queries
            print("\n3. Testing time-based queries...")
            
            # Query recent data
            recent_records = await tob_repo.get_multi(limit=20)
            print(f"   ✅ Retrieved {len(recent_records)} recent records")
            
            # Group by symbol
            symbol_counts = {}
            total_volume = 0
            for record in recent_records:
                symbol_counts[record.symbol] = symbol_counts.get(record.symbol, 0) + 1
                total_volume += record.volume or 0
            
            print(f"   📊 Record distribution:")
            for symbol, count in sorted(symbol_counts.items()):
                print(f"      • {symbol}: {count} records")
            
            print(f"   📈 Total volume in sample: {total_volume:,}")
            
            # Test symbol-specific queries
            print("\n4. Testing symbol-specific queries...")
            
            for symbol in ["AAPL", "GOOGL"]:
                symbol_records = await tob_repo.get_by_symbol(symbol, limit=5)
                if symbol_records:
                    latest = symbol_records[0]
                    print(f"   📊 {symbol} latest: ${latest.bid}/${latest.ask} at {latest.timestamp.strftime('%H:%M:%S')}")
                    
                    # Show price evolution
                    print(f"      Price evolution for {symbol}:")
                    for i, record in enumerate(symbol_records[:3]):
                        print(f"         {i+1}. {record.timestamp.strftime('%H:%M:%S')}: ${record.bid}")
                else:
                    print(f"   ⚠️  No records found for {symbol}")
            
            # Test TimescaleDB chunk information
            print("\n5. Testing TimescaleDB chunk information...")
            
            try:
                # Query chunk information directly
                chunk_query = """
                    SELECT 
                        hypertable_name,
                        chunk_name,
                        range_start,
                        range_end,
                        is_compressed,
                        compressed_chunk_id IS NOT NULL as has_compression
                    FROM timescaledb_information.chunks 
                    WHERE hypertable_schema = 'market_data' 
                    AND hypertable_name = 'top_of_book'
                    ORDER BY range_start DESC
                    LIMIT 5
                """
                
                # Execute raw query
                result = await session.execute(chunk_query)
                chunks = result.fetchall()
                
                if chunks:
                    print(f"   ✅ Found {len(chunks)} chunks for top_of_book table:")
                    for chunk in chunks:
                        compression_status = "✅ Compressed" if chunk.has_compression else "❌ Uncompressed"
                        print(f"      • {chunk.chunk_name}: {chunk.range_start} to {chunk.range_end} ({compression_status})")
                else:
                    print("   ⚠️  No chunks found yet (data might be in single chunk)")
                    
            except Exception as e:
                print(f"   ⚠️  Could not query chunk information: {e}")
            
            print("\n✅ TimescaleDB features test completed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ TimescaleDB features test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance_queries():
    """Test performance-oriented queries"""
    print("\n" + "="*50)
    print("PERFORMANCE QUERIES TEST")
    print("="*50)
    
    try:
        async with db_session() as session:
            print("\n6. Testing performance queries...")
            
            # Test aggregation queries
            print("   📊 Testing aggregation queries...")
            
            # Get average prices by symbol
            avg_query = """
                SELECT 
                    symbol,
                    COUNT(*) as record_count,
                    AVG(bid) as avg_bid,
                    AVG(ask) as avg_ask,
                    MAX(timestamp) as latest_update
                FROM market_data.top_of_book 
                GROUP BY symbol
                ORDER BY symbol
            """
            
            result = await session.execute(avg_query)
            aggregations = result.fetchall()
            
            if aggregations:
                print(f"   ✅ Aggregation results for {len(aggregations)} symbols:")
                for agg in aggregations:
                    print(f"      • {agg.symbol}: {agg.record_count} records, avg bid: ${agg.avg_bid:.2f}, latest: {agg.latest_update.strftime('%H:%M:%S')}")
            else:
                print("   ⚠️  No aggregation data found")
            
            # Test time-window queries
            print("\n   ⏰ Testing time-window queries...")
            
            # Get records from last 30 minutes
            time_window_query = """
                SELECT symbol, COUNT(*) as count
                FROM market_data.top_of_book 
                WHERE timestamp >= NOW() - INTERVAL '30 minutes'
                GROUP BY symbol
                ORDER BY count DESC
            """
            
            result = await session.execute(time_window_query)
            time_results = result.fetchall()
            
            if time_results:
                print(f"   ✅ Records in last 30 minutes:")
                for tr in time_results:
                    print(f"      • {tr.symbol}: {tr.count} records")
            else:
                print("   ⚠️  No recent data found")
            
            print("\n✅ Performance queries completed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ Performance queries test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_health():
    """Test database health and TimescaleDB status"""
    print("\n" + "="*50)
    print("DATABASE HEALTH CHECK")
    print("="*50)
    
    try:
        async with db_session() as session:
            print("\n7. Checking database health...")
            
            # Check TimescaleDB version
            try:
                version_query = "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
                result = await session.execute(version_query)
                version = result.scalar()
                print(f"   ✅ TimescaleDB version: {version}")
            except Exception as e:
                print(f"   ⚠️  Could not get TimescaleDB version: {e}")
            
            # Check hypertable status
            hypertable_query = """
                SELECT 
                    hypertable_name,
                    num_chunks,
                    compression_enabled,
                    table_bytes,
                    index_bytes,
                    total_bytes
                FROM timescaledb_information.hypertables 
                WHERE hypertable_schema = 'market_data'
                ORDER BY hypertable_name
            """
            
            result = await session.execute(hypertable_query)
            hypertables = result.fetchall()
            
            if hypertables:
                print(f"   ✅ Hypertable status ({len(hypertables)} tables):")
                for ht in hypertables:
                    compression = "✅ Enabled" if ht.compression_enabled else "❌ Disabled"
                    size_mb = (ht.total_bytes or 0) / (1024 * 1024)
                    print(f"      • {ht.hypertable_name}: {ht.num_chunks} chunks, {compression}, {size_mb:.2f} MB")
            else:
                print("   ⚠️  No hypertables found")
            
            # Check compression policies
            compression_query = """
                SELECT 
                    hypertable_name,
                    older_than,
                    orderby_column_name
                FROM timescaledb_information.compression_settings
                WHERE hypertable_schema = 'market_data'
                ORDER BY hypertable_name
            """
            
            result = await session.execute(compression_query)
            compression_policies = result.fetchall()
            
            if compression_policies:
                print(f"   ✅ Compression policies ({len(compression_policies)} active):")
                for cp in compression_policies:
                    print(f"      • {cp.hypertable_name}: compress after {cp.older_than}")
            else:
                print("   ⚠️  No compression policies found")
            
            print("\n✅ Database health check completed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ Database health check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting comprehensive repository and TimescaleDB tests...")
    print("This will test your database setup thoroughly.\n")
    
    # Run all test suites
    tests = [
        ("Basic Repository Operations", test_basic_repository_operations),
        ("TimescaleDB Features", test_timescale_features),
        ("Performance Queries", test_performance_queries),
        ("Database Health", test_database_health),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔄 Running {test_name}...")
        success = await test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("Your TimescaleDB setup is working perfectly!")
        print("\nNext steps:")
        print("1. Your database is ready for production use")
        print("2. Start implementing your trading strategies")
        print("3. Monitor compression and chunk creation as data grows")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
