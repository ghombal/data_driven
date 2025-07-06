# src/database/schemas/responses.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field

from .market_data import BaseSchema

class PaginationMeta(BaseSchema):
    """Pagination metadata"""
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=1000)
    total: int = Field(..., ge=0)
    pages: int = Field(..., ge=0)
    has_prev: bool
    has_next: bool

class PaginatedResponse(BaseSchema):
    """Base paginated response"""
    data: List[Any]
    meta: PaginationMeta

class HealthCheckResponse(BaseSchema):
    """Health check response"""
    status: str
    timestamp: datetime
    database_connected: bool
    tables_count: int
    version: str

class DatabaseStatsResponse(BaseSchema):
    """Database statistics response"""
    total_records: Dict[str, int]
    database_size: str
    table_sizes: Dict[str, str]
    compression_stats: Dict[str, Any]
    performance_metrics: Dict[str, float]
    timestamp: datetime

class MarketDepthSnapshot(BaseSchema):
    """Market depth snapshot"""
    symbol: str
    bids: List[Dict[str, Any]]
    asks: List[Dict[str, Any]]
    timestamp: datetime
    spread: Optional[Decimal] = None

class TimeSeriesData(BaseSchema):
    """Time series data response"""
    symbol: str
    data_type: str
    start_time: datetime
    end_time: datetime
    interval: Optional[str] = None
    data: List[Dict[str, Any]]
    count: int

class PerformanceReport(BaseSchema):
    """Performance report response"""
    period: str
    metrics: Dict[str, float]
    symbols: List[str]
    total_messages: int
    average_latency: float
    error_rate: float
    timestamp: datetime

class ErrorResponse(BaseSchema):
    """Error response schema"""
    error: str
    message: str
    timestamp: datetime
    request_id: Optional[str] = None
