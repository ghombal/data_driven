# src/database/repositories/base.py
from typing import TypeVar, Generic, List, Optional, Any, Dict
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel

from src.database.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """Base repository with common CRUD operations"""
    
    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model
    
    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record"""
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def create_batch(self, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """Create multiple records in batch"""
        db_objs = []
        for obj_in in objs_in:
            obj_data = obj_in.model_dump()
            db_obj = self.model(**obj_data)
            db_objs.append(db_obj)
        
        self.session.add_all(db_objs)
        await self.session.commit()
        
        # Refresh all objects
        for db_obj in db_objs:
            await self.session.refresh(db_obj)
        
        return db_objs
    
    async def get(self, id: Any) -> Optional[ModelType]:
        """Get a single record by ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[ModelType]:
        """Get multiple records with pagination"""
        query = select(self.model)
        
        if order_by:
            order_column = getattr(self.model, order_by, None)
            if order_column:
                query = query.order_by(desc(order_column) if order_desc else asc(order_column))
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count(self) -> int:
        """Count total records"""
        result = await self.session.execute(
            select(func.count(self.model.id))
        )
        return result.scalar()
    
    async def delete(self, *, id: Any) -> Optional[ModelType]:
        """Delete a record by ID"""
        db_obj = await self.get(id)
        if db_obj:
            await self.session.delete(db_obj)
            await self.session.commit()
        return db_obj
    
    async def delete_batch(self, *, ids: List[Any]) -> int:
        """Delete multiple records by IDs"""
        result = await self.session.execute(
            select(self.model).where(self.model.id.in_(ids))
        )
        db_objs = result.scalars().all()
        
        for db_obj in db_objs:
            await self.session.delete(db_obj)
        
        await self.session.commit()
        return len(db_objs)
    
    async def get_by_time_range(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        limit: int = 1000
    ) -> List[ModelType]:
        """Get records within time range (for time-series data)"""
        # Check if model has timestamp field
        if not hasattr(self.model, 'timestamp'):
            raise ValueError(f"Model {self.model.__name__} does not have timestamp field")
        
        query = select(self.model).where(
            and_(
                self.model.timestamp >= start_time,
                self.model.timestamp <= end_time
            )
        ).order_by(desc(self.model.timestamp)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def cleanup_old_records(self, older_than: datetime) -> int:
        """Clean up records older than specified time"""
        if not hasattr(self.model, 'timestamp'):
            raise ValueError(f"Model {self.model.__name__} does not have timestamp field")
        
        result = await self.session.execute(
            select(self.model).where(self.model.timestamp < older_than)
        )
        db_objs = result.scalars().all()
        
        for db_obj in db_objs:
            await self.session.delete(db_obj)
        
        await self.session.commit()
        return len(db_objs)