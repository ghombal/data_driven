# src/database/config.py
import os
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "market_data_dev"
    username: str = "market_user"
    password: str = "your_password_here"
    echo: bool = False
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600

class TimescaleConfig(BaseModel):
    """TimescaleDB specific configuration"""
    chunk_time_interval: str = "30 minutes"
    compression_after: str = "2 hours"
    compression_policy: str = "lz4"
    retention_policy: str = "7 days"

class SymbolsConfig(BaseModel):
    """Symbols and processing configuration"""
    development: list[str] = [
        'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 
        'META', 'NVDA', 'NFLX', 'SPY', 'QQQ'
    ]
    batch_size: int = 5000
    flush_interval: int = 2
    max_queue_size: int = 50000

class PerformanceConfig(BaseModel):
    """Performance configuration"""
    connection_pool_size: int = 25
    statement_timeout: int = 30000
    query_timeout: int = 10000
    batch_insert_size: int = 1000

class Settings(BaseSettings):
    """Application settings"""
    database: DatabaseConfig = DatabaseConfig()
    timescale: TimescaleConfig = TimescaleConfig()
    symbols: SymbolsConfig = SymbolsConfig()
    performance: PerformanceConfig = PerformanceConfig()
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"

def load_config(config_path: Optional[str] = None) -> Settings:
    """Load configuration from YAML file"""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "database.yaml"
    
    if not Path(config_path).exists():
        # Return default configuration
        return Settings()
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Get environment (default to development)
    environment = os.getenv('ENVIRONMENT', 'development')
    
    # Extract configuration for current environment
    db_config = config_data.get('database', {}).get(environment, {})
    timescale_config = config_data.get('timescale', {})
    symbols_config = config_data.get('symbols', {})
    performance_config = config_data.get('performance', {})
    
    return Settings(
        database=DatabaseConfig(**db_config),
        timescale=TimescaleConfig(**timescale_config),
        symbols=SymbolsConfig(**symbols_config),
        performance=PerformanceConfig(**performance_config)
    )

# Global configuration instance
settings = load_config()
