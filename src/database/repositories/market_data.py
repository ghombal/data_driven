# src/database/repositories/market_data.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_, desc, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repositories.base import BaseRepository
from ..models.market_data import (
    TopOfBook, TickByTick, MarketDepth, HistoricalBar, 
    FundamentalData, PerformanceMetric, MarketSide
)
from ..schemas.market_data import (
    TopOfBookCreate, TickByTickCreate, MarketDepthCreate,
    HistoricalBarCreate, FundamentalDataCreate, PerformanceMetricCreate
)

class TopOfBookRepository(BaseRepository[TopOfBook, TopOfBookCreate, TopOfBookCreate]):
    """Repository for top of book data"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, TopOfBook)
    
    async def get_latest_by_symbol(self, symbol: str, limit: int = 100) -> List[TopOfBook]:
        """Get latest top of book data for a symbol"""
        query = select(self.model).where(
            self.model.symbol == symbol
        ).order_by(desc(self.model.timestamp)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_latest_all_symbols(self) -> List[TopOfBook]:
        """Get latest top of book data for all symbols"""
        # Get latest timestamp for each symbol
        subquery = select(
            self.model.symbol,
            func.max(self.model.timestamp).label('max_timestamp')
        ).group_by(self.model.symbol).subquery()
        
        query = select(self.model).join(
            subquery,
            and_(
                self.model.symbol == subquery.c.symbol,
                self.model.timestamp == subquery.c.max_timestamp
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_price_history(
        self, 
        symbol: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get price history for a symbol"""
        query = select(
            self.model.timestamp,
            self.model.last,
            self.model.volume
        ).where(
            and_(
                self.model.symbol == symbol,
                self.model.timestamp >= start_time,
                self.model.timestamp <= end_time,
                self.model.last.is_not(None)
            )
        ).order_by(self.model.timestamp)
        
        result = await self.session.execute(query)
        return [
            {
                'timestamp': row.timestamp,
                'price': row.last,
                'volume': row.volume
            }
            for row in result
        ]

class TickByTickRepository(BaseRepository[TickByTick, TickByTickCreate, TickByTickCreate]):
    """Repository for tick by tick data"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, TickByTick)
    
    async def get_ticks_by_symbol(
        self, 
        symbol: str, 
        start_time: datetime, 
        end_time: datetime,
        tick_type: Optional[str] = None
    ) -> List[TickByTick]:
        """Get ticks for a symbol within time range"""
        conditions = [
            self.model.symbol == symbol,
            self.model.timestamp >= start_time,
            self.model.timestamp <= end_time
        ]
        
        if tick_type:
            conditions.append(self.model.tick_type == tick_type)
        
        query = select(self.model).where(and_(*conditions)).order_by(self.model.timestamp)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_volume_profile(
        self, 
        symbol: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get volume profile for a symbol"""
        query = select(
            func.date_trunc('minute', self.model.timestamp).label('minute'),
            func.sum(self.model.size).label('total_volume'),
            func.count(self.model.id).label('tick_count')
        ).where(
            and_(
                self.model.symbol == symbol,
                self.model.timestamp >= start_time,
                self.model.timestamp <= end_time
            )
        ).group_by('minute').order_by('minute')
        
        result = await self.session.execute(query)
        return [
            {
                'minute': row.minute,
                'total_volume': row.total_volume,
                'tick_count': row.tick_count
            }
            for row in result
        ]

class MarketDepthRepository(BaseRepository[MarketDepth, MarketDepthCreate, MarketDepthCreate]):
    """Repository for market depth data"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, MarketDepth)
    
    async def get_current_depth(self, symbol: str, levels: int = 10) -> Dict[str, List[Dict]]:
        """Get current market depth for a symbol"""
        # Get latest timestamp for the symbol
        latest_time_query = select(
            func.max(self.model.timestamp)
        ).where(self.model.symbol == symbol)
        
        latest_time_result = await self.session.execute(latest_time_query)
        latest_time = latest_time_result.scalar()
        
        if not latest_time:
            return {'bids': [], 'asks': []}
        
        # Get depth data from the latest time
        time_window = latest_time - timedelta(seconds=10)  # 10 second window
        
        query = select(self.model).where(
            and_(
                self.model.symbol == symbol,
                self.model.timestamp >= time_window
            )
        ).order_by(desc(self.model.timestamp))
        
        result = await self.session.execute(query)
        depth_data = result.scalars().all()
        
        # Process depth data
        bids = {}
        asks = {}
        
        for depth in depth_data:
            if depth.side == MarketSide.BID:
                if depth.position not in bids:
                    bids[depth.position] = {
                        'position': depth.position,
                        'price': depth.price,
                        'size': depth.size,
                        'timestamp': depth.timestamp
                    }
            else:
                if depth.position not in asks:
                    asks[depth.position] = {
                        'position': depth.position,
                        'price': depth.price,
                        'size': depth.size,
                        'timestamp': depth.timestamp
                    }
        
        # Sort and limit
        sorted_bids = sorted(bids.values(), key=lambda x: x['position'])[:levels]
        sorted_asks = sorted(asks.values(), key=lambda x: x['position'])[:levels]
        
        return {'bids': sorted_bids, 'asks': sorted_asks}

class HistoricalBarRepository(BaseRepository[HistoricalBar, HistoricalBarCreate, HistoricalBarCreate]):
    """Repository for historical bar data"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, HistoricalBar)
    
    async def get_bars_by_symbol(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[HistoricalBar]:
        """Get historical bars for a symbol"""
        query = select(self.model).where(
            and_(
                self.model.symbol == symbol,
                self.model.date >= start_date.date(),
                self.model.date <= end_date.date()
            )
        ).order_by(self.model.date)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_price_statistics(
        self, 
        symbol: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get price statistics for a symbol"""
        start_date = datetime.now().date() - timedelta(days=days)
        
        query = select(
            func.avg(self.model.close).label('avg_price'),
            func.max(self.model.high).label('max_price'),
            func.min(self.model.low).label('min_price'),
            func.sum(self.model.volume).label('total_volume'),
            func.count(self.model.id).label('bar_count')
        ).where(
            and_(
                self.model.symbol == symbol,
                self.model.date >= start_date
            )
        )
        
        result = await self.session.execute(query)
        row = result.first()
        
        return {
            'symbol': symbol,
            'period_days': days,
            'avg_price': row.avg_price,
            'max_price': row.max_price,
            'min_price': row.min_price,
            'total_volume': row.total_volume,
            'bar_count': row.bar_count
        }

class PerformanceMetricRepository(BaseRepository[PerformanceMetric, PerformanceMetricCreate, PerformanceMetricCreate]):
    """Repository for performance metrics"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PerformanceMetric)
    
    async def get_metrics_by_name(
        self, 
        metric_name: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[PerformanceMetric]:
        """Get performance metrics by name"""
        query = select(self.model).where(
            and_(
                self.model.metric_name == metric_name,
                self.model.timestamp >= start_time,
                self.model.timestamp <= end_time
            )
        ).order_by(self.model.timestamp)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_latest_metrics(self) -> List[PerformanceMetric]:
        """Get latest performance metrics"""
        subquery = select(
            self.model.metric_name,
            func.max(self.model.timestamp).label('max_timestamp')
        ).group_by(self.model.metric_name).subquery()
        
        query = select(self.model).join(
            subquery,
            and_(
                self.model.metric_name == subquery.c.metric_name,
                self.model.timestamp == subquery.c.max_timestamp
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
