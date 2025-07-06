# src/scripts/test_schemas.py
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.schemas.market_data import (
    TopOfBookCreate, TickByTickCreate, MarketDepthCreate,
    HistoricalBarCreate, MarketSide, TickType, OrderOperation
)

def test_schemas():
    """Test all Pydantic schemas"""
    print("Testing Pydantic schemas...")
    
    # Test TopOfBookCreate
    try:
        top_of_book = TopOfBookCreate(
            symbol="AAPL",
            bid=Decimal("150.25"),
            ask=Decimal("150.26"),
            last=Decimal("150.25"),
            volume=1000,
            timestamp=datetime.utcnow()
        )
        print("✅ TopOfBookCreate schema works")
        print(f"   Data: {top_of_book.symbol} - ${top_of_book.last}")
    except Exception as e:
        print(f"❌ TopOfBookCreate schema failed: {e}")
        return False
    
    # Test TickByTickCreate
    try:
        tick_data = TickByTickCreate(
            symbol="GOOGL",
            tick_type=TickType.LAST,
            price=Decimal("140.50"),
            size=100,
            timestamp=datetime.utcnow()
        )
        print("✅ TickByTickCreate schema works")
        print(f"   Data: {tick_data.symbol} - ${tick_data.price} x {tick_data.size}")
    except Exception as e:
        print(f"❌ TickByTickCreate schema failed: {e}")
        return False
    
    # Test MarketDepthCreate
    try:
        depth_data = MarketDepthCreate(
            symbol="TSLA",
            position=0,
            operation=OrderOperation.UPDATE,
            side=MarketSide.BID,
            price=Decimal("200.00"),
            size=500,
            timestamp=datetime.utcnow()
        )
        print("✅ MarketDepthCreate schema works")
        print(f"   Data: {depth_data.symbol} - {depth_data.side} ${depth_data.price}")
    except Exception as e:
        print(f"❌ MarketDepthCreate schema failed: {e}")
        return False
    
    # Test validation
    try:
        # This should fail - negative price
        bad_data = TopOfBookCreate(
            symbol="TEST",
            bid=Decimal("-10.00"),  # Negative price should fail
            ask=Decimal("150.26"),
            last=Decimal("150.25"),
            volume=1000
        )
        print("❌ Validation should have failed for negative price")
        return False
    except ValueError as e:
        print("✅ Validation correctly rejected negative price")
        print(f"   Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error in validation test: {e}")
        return False
    
    return True

def main():
    """Run schema tests"""
    print("="*50)
    print("PYDANTIC SCHEMA TESTS")
    print("="*50)
    
    if test_schemas():
        print("\n✅ All schema tests passed!")
        print("Phase 3 complete - Pydantic schemas working correctly")
        return True
    else:
        print("\n❌ Some schema tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)