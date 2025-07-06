# src/database/models/market_data.py
from datetime import datetime, date
from typing import Optional, Any
from decimal import Decimal
from sqlalchemy import (
    String, Integer, Numeric, BigInteger, Date, 
    Text, Index, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins import MarketDataMixin, SymbolMixin

# Enums
import enum

class MarketSide(str, enum.Enum):
    BID = "bid"
    ASK = "ask"

class TickType(str, enum.Enum):
    LAST = "last"
    BID = "bid"
    ASK = "ask"
    MIDPOINT = "midpoint"

class OrderOperation(str, enum.Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"

class TopOfBook(Base, MarketDataMixin):
    """Top of book market data"""
    __tablename__ = "top_of_book"
    __table_args__ = (
        Index('idx_top_of_book_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_top_of_book_timestamp', 'timestamp'),
        {'schema': 'market_data'}
    )
    
    bid: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 4), 
        nullable=True
    )
    ask: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 4), 
        nullable=True
    )
    last: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 4), 
        nullable=True
    )
    volume: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<TopOfBook(symbol={self.symbol}, timestamp={self.timestamp})>"

class TickByTick(Base, MarketDataMixin):
    """Tick by tick market data"""
    __tablename__ = "tick_by_tick"
    __table_args__ = (
        Index('idx_tick_by_tick_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_tick_by_tick_tick_type', 'tick_type'),
        {'schema': 'market_data'}
    )
    
    tick_type: Mapped[TickType] = mapped_column(
        SQLEnum(TickType, name='tick_type'),
        nullable=False
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), 
        nullable=False
    )
    size: Mapped[int] = mapped_column(
        Integer, 
        nullable=False
    )
    tick_attrib: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<TickByTick(symbol={self.symbol}, price={self.price})>"

class MarketDepth(Base, MarketDataMixin):
    """Market depth (Level 2) data"""
    __tablename__ = "market_depth"
    __table_args__ = (
        Index('idx_market_depth_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_market_depth_side', 'side'),
        {'schema': 'market_data'}
    )
    
    position: Mapped[int] = mapped_column(
        Integer, 
        nullable=False
    )
    operation: Mapped[OrderOperation] = mapped_column(
        SQLEnum(OrderOperation, name='order_operation'),
        nullable=False
    )
    side: Mapped[MarketSide] = mapped_column(
        SQLEnum(MarketSide, name='market_side'),
        nullable=False
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), 
        nullable=False
    )
    size: Mapped[int] = mapped_column(
        Integer, 
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<MarketDepth(symbol={self.symbol}, side={self.side})>"

class HistoricalBar(Base, SymbolMixin):
    """Historical bar data"""
    __tablename__ = "historical_bars"
    __table_args__ = (
        Index('idx_historical_bars_symbol_date', 'symbol', 'date'),
        {'schema': 'market_data'}
    )
    
    date: Mapped[date] = mapped_column(
        Date, 
        nullable=False
    )
    open: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), 
        nullable=False
    )
    high: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), 
        nullable=False
    )
    low: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), 
        nullable=False
    )
    close: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), 
        nullable=False
    )
    volume: Mapped[int] = mapped_column(
        BigInteger, 
        nullable=False
    )
    bar_count: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )
    average: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 4), 
        nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<HistoricalBar(symbol={self.symbol}, date={self.date})>"

class FundamentalData(Base, SymbolMixin):
    """Fundamental data storage"""
    __tablename__ = "fundamental_data"
    __table_args__ = (
        Index('idx_fundamental_data_symbol_report_type', 'symbol', 'report_type'),
        {'schema': 'market_data'}
    )
    
    report_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False
    )
    data: Mapped[str] = mapped_column(
        Text, 
        nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<FundamentalData(symbol={self.symbol}, report_type={self.report_type})>"

class PerformanceMetric(Base):
    """Performance monitoring metrics"""
    __tablename__ = "performance_metrics"
    __table_args__ = (
        Index('idx_performance_metrics_name_timestamp', 'metric_name', 'timestamp'),
        {'schema': 'market_data'}
    )
    
    metric_name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False
    )
    metric_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), 
        nullable=False
    )
    symbol: Mapped[Optional[str]] = mapped_column(
        String(20), 
        nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        nullable=False
    )
    metric_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<PerformanceMetric(name={self.metric_name}, value={self.metric_value})>"
