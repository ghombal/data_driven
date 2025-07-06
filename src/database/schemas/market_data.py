# src/database/schemas/market_data.py
from datetime import datetime, date
from typing import Optional, Any, Dict, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum

class MarketSide(str, Enum):
    BID = "bid"
    ASK = "ask"

class TickType(str, Enum):
    LAST = "last"
    BID = "bid"
    ASK = "ask"
    MIDPOINT = "midpoint"

class OrderOperation(str, Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"

class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        arbitrary_types_allowed=True
    )

class TopOfBookCreate(BaseSchema):
    """Schema for creating top of book records"""
    symbol: str = Field(..., min_length=1, max_length=20)
    bid: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    ask: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    last: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    volume: Optional[int] = Field(None, ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('ask', 'bid', 'last')
    @classmethod
    def validate_prices(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price cannot be negative')
        return v

class TopOfBookResponse(BaseSchema):
    """Schema for top of book responses"""
    id: str
    symbol: str
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    last: Optional[Decimal]
    volume: Optional[int]
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

class TickByTickCreate(BaseSchema):
    """Schema for creating tick by tick records"""
    symbol: str = Field(..., min_length=1, max_length=20)
    tick_type: TickType = TickType.LAST
    price: Decimal = Field(..., gt=0, decimal_places=4)
    size: int = Field(..., gt=0)
    tick_attrib: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TickByTickResponse(BaseSchema):
    """Schema for tick by tick responses"""
    id: str
    symbol: str
    tick_type: TickType
    price: Decimal
    size: int
    tick_attrib: Optional[Dict[str, Any]]
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

class MarketDepthCreate(BaseSchema):
    """Schema for creating market depth records"""
    symbol: str = Field(..., min_length=1, max_length=20)
    position: int = Field(..., ge=0, le=20)
    operation: OrderOperation = OrderOperation.UPDATE
    side: MarketSide
    price: Decimal = Field(..., gt=0, decimal_places=4)
    size: int = Field(..., ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MarketDepthResponse(BaseSchema):
    """Schema for market depth responses"""
    id: str
    symbol: str
    position: int
    operation: OrderOperation
    side: MarketSide
    price: Decimal
    size: int
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

class HistoricalBarCreate(BaseSchema):
    """Schema for creating historical bar records"""
    symbol: str = Field(..., min_length=1, max_length=20)
    date: date
    open: Decimal = Field(..., gt=0, decimal_places=4)
    high: Decimal = Field(..., gt=0, decimal_places=4)
    low: Decimal = Field(..., gt=0, decimal_places=4)
    close: Decimal = Field(..., gt=0, decimal_places=4)
    volume: int = Field(..., ge=0)
    bar_count: Optional[int] = Field(None, ge=0)
    average: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    
    @field_validator('high')
    @classmethod
    def validate_high(cls, v, info):
        if 'low' in info.data and v < info.data['low']:
            raise ValueError('High must be >= low')
        return v

class HistoricalBarResponse(BaseSchema):
    """Schema for historical bar responses"""
    id: str
    symbol: str
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    bar_count: Optional[int]
    average: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

class FundamentalDataCreate(BaseSchema):
    """Schema for creating fundamental data records"""
    symbol: str = Field(..., min_length=1, max_length=20)
    report_type: str = Field(..., min_length=1, max_length=50)
    data: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FundamentalDataResponse(BaseSchema):
    """Schema for fundamental data responses"""
    id: str
    symbol: str
    report_type: str
    data: str
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

class PerformanceMetricCreate(BaseSchema):
    """Schema for creating performance metrics"""
    metric_name: str = Field(..., min_length=1, max_length=100)
    metric_value: Decimal = Field(..., decimal_places=4)
    symbol: Optional[str] = Field(None, max_length=20)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class PerformanceMetricResponse(BaseSchema):
    """Schema for performance metric responses"""
    id: str
    metric_name: str
    metric_value: Decimal
    symbol: Optional[str]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

# Batch schemas
class BatchInsertResponse(BaseSchema):
    """Schema for batch insert responses"""
    inserted_count: int
    failed_count: int
    errors: List[str] = []
    execution_time: float

class MarketDataSummary(BaseSchema):
    """Schema for market data summary"""
    symbol: str
    latest_price: Optional[Decimal]
    volume: Optional[int]
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    spread: Optional[Decimal]
    last_updated: datetime