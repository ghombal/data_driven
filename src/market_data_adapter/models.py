from typing import Optional, List, Union, Any
from datetime import datetime
from pydantic import BaseModel


class TopOfBookMessage(BaseModel):
    event_type: str = "top_of_book"
    symbol: str
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]
    volume: Optional[int]
    timestamp: Optional[datetime]


class TickByTickMessage(BaseModel):
    event_type: str
    symbol: str
    time: Optional[datetime]
    price: Optional[float]
    size: Optional[int]
    tickAttrib: Optional[dict[str, bool]] = None


class MarketDepthMessage(BaseModel):
    event_type: str = "market_depth"
    symbol: str
    position: int
    operation: int  # 0=insert,1=update,2=delete
    side: int       # 0=bid,1=ask
    price: float
    size: int


class HistoricalBar(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    barCount: Optional[int] = None
    average: Optional[float] = None


class HistoricalDataResponse(BaseModel):
    event_type: str = "historical_data"
    symbol: str
    bars: List[HistoricalBar]


class FundamentalDataResponse(BaseModel):
    event_type: str = "fundamental_data"
    symbol: str
    report_type: str
    data: Union[str, list, dict, Any]
    


class FundamentalRatiosResponse(BaseModel):
    event_type: str = "fundamental_ratios"
    symbol: str
    data: Union[str, list, dict, Any]

MarketDataEvent = Union[
    TopOfBookMessage,
    TickByTickMessage,
    MarketDepthMessage
]
