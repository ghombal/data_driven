# src/database/models/mixins.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

class SymbolMixin:
    """Mixin for tables that have a symbol column"""
    symbol: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        index=True
    )

class TimestampMixin:
    """Mixin for tables that have a timestamp column (for time-series data)"""
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

class MarketDataMixin(SymbolMixin, TimestampMixin):
    """Combined mixin for market data tables"""
    pass

class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        self.deleted_at = datetime.utcnow()
