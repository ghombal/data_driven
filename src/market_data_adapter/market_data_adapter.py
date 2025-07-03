import asyncio
from ib_insync import *
import logging
from datetime import datetime
from models import (
    TopOfBookMessage,
    TickByTickMessage,
    MarketDepthMessage,
    HistoricalDataResponse,
    FundamentalDataResponse,
    FundamentalRatiosResponse,
    HistoricalBar,
)
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketDataAdapter:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
        queue_maxsize: int = 10000,
    ):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib: Optional[IB] = None
        self.contracts: dict[str, Contract] = {}
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=queue_maxsize)
        self.ticker_subs: dict[str, Ticker] = {}
        self.l2_depth_subs: dict[str, object] = {}

    async def connect(self) -> None:
        logger.info("Connecting to IBKR...")
        self.ib = IB()
        await self.ib.connectAsync(self.host, self.port, clientId=self.client_id, timeout=10)
        logger.info("Connected.")
        
    
    # ✅ CHANGE 6: Add cleanup method (recommended)
    def cleanup_subscriptions(self) -> None:
        """Clean up all active subscriptions"""
        # Cancel market data subscriptions
        for symbol, ticker in self.ticker_subs.items():
            try:
                if hasattr(ticker, 'contract') and ticker.contract:
                    self.ib.cancelMktData(ticker.contract)
                    logger.info(f"Cancelled market data subscription for {symbol}")
            except Exception as e:
                logger.warning(f"Error cancelling market data subscription for {symbol}: {e}")
        
        # Cancel market depth subscriptions
        for symbol, ticker in self.l2_depth_subs.items():
            try:
                if hasattr(ticker, 'contract') and ticker.contract:
                    self.ib.cancelMktDepth(ticker.contract, isSmartDepth=False)
                    logger.info(f"Cancelled market depth subscription for {symbol}")
            except Exception as e:
                logger.warning(f"Error cancelling market depth subscription for {symbol}: {e}")
        
        # Clear subscription storage
        self.ticker_subs.clear()
        self.l2_depth_subs.clear()

    async def disconnect(self) -> None:
        if self.ib:
            self.cleanup_subscriptions()  # Add this line
            self.ib.disconnect()
            logger.info("Disconnected.")
    
   

    def define_contracts(self, symbol_list: list[str], exchange: str = "SMART", currency: str = "USD") -> None:
        for sym in symbol_list:
            contract = Stock(sym, exchange, currency)
            self.contracts[sym] = contract
            logger.info(f"Defined contract for {sym}: {contract}")

    async def subscribe_top_of_book(self, symbol: str) -> None:
        if symbol not in self.contracts:
            raise ValueError(f"Symbol {symbol} not defined. Call define_contracts first.")
        contract = self.contracts[symbol]
        ticker = self.ib.reqMktData(contract, snapshot=False)

        async def monitor():
            prev_snapshot = None
            while True:
                try:
                    snapshot_dict = self.normalize_ticker(ticker)
                    snapshot = TopOfBookMessage(**snapshot_dict)
                    if snapshot != prev_snapshot:
                        prev_snapshot = snapshot
                        await self.queue.put(snapshot)
                except Exception as e:
                    logger.warning(f"Error creating TopOfBookMessage for {symbol}: {e}")           
                await asyncio.sleep(0.1)

        asyncio.create_task(monitor())
        self.ticker_subs[symbol] = ticker
        logger.info(f"Subscribed to top-of-book for {symbol}")

# FIXED CODE:
    async def subscribe_tick_by_tick(self, symbol: str, tickType: str = "Last") -> None:
        if symbol not in self.contracts:
            raise ValueError(f"Symbol {symbol} not defined.")

        contract = self.contracts[symbol]

    # Create the tick-by-tick subscription (NO callback parameter)
        ticker = self.ib.reqTickByTickData(contract, tickType=tickType, numberOfTicks=0, ignoreSize=False)
    
    # Store the ticker for cleanup
        self.ticker_subs[f"{symbol}_tick_{tickType}"] = ticker

    # Monitor ticker's tickByTicks list in a separate task
        async def monitor_ticks():
            last_processed_count = 0
            while True:
                await asyncio.sleep(0.01)
            
            # Check if there are new ticks
                if ticker.tickByTicks and len(ticker.tickByTicks) > last_processed_count:
                # Process only new ticks
                    new_ticks = ticker.tickByTicks[last_processed_count:]
                
                    for tick in new_ticks:
                        message = TickByTickMessage(
                            event_type=f"tick_by_tick_{tickType.lower()}",
                            symbol=symbol,
                            time=tick.time,
                            price=tick.price,
                            size=tick.size,
                            tickAttrib=getattr(tick, 'tickAttribLast', getattr(tick, 'tickAttrib', None)).__dict__ if hasattr(tick, 'tickAttribLast') or hasattr(tick, 'tickAttrib') else None,
                        )
                        await self.queue.put(message)
                
                    last_processed_count = len(ticker.tickByTicks)

    # Start monitoring task
        asyncio.create_task(monitor_ticks())
    
        logger.info(f"Subscribed to tick-by-tick [{tickType}] for {symbol}")
    
    async def subscribe_order_book(self, symbol: str, numRows: int = 5) -> None:
        """Alternative implementation using ticker's updateEvent"""
        if symbol not in self.contracts:
            raise ValueError(f"Symbol {symbol} not defined.")

        contract = self.contracts[symbol]

        # Create the market depth subscription
        ticker = self.ib.reqMktDepth(contract, numRows=numRows, isSmartDepth=False)
        
        # Store the ticker for cleanup
        self.l2_depth_subs[symbol] = ticker

        def on_depth_update(ticker):
            # Process bid side
            for i, bid in enumerate(ticker.domBids):
                message = MarketDepthMessage(
                    symbol=symbol,
                    position=i,
                    operation=1,  # Update operation
                    side=0,       # Bid side
                    price=bid.price,
                    size=bid.size,
                )
                asyncio.create_task(self.queue.put(message))
            
            # Process ask side
            for i, ask in enumerate(ticker.domAsks):
                message = MarketDepthMessage(
                    symbol=symbol,
                    position=i,
                    operation=1,  # Update operation
                    side=1,       # Ask side
                    price=ask.price,
                    size=ask.size,
                )
                asyncio.create_task(self.queue.put(message))

        # Connect to ticker's update event
        ticker.updateEvent += on_depth_update
        
        logger.info(f"Subscribed to market depth for {symbol} (v2)")


        
    async def subscribe_smart_depth(self, symbol: str, numRows: int = 10) -> None:
        """
        Subscribe to L3 market depth (Smart Depth) with error handling
        """
        if symbol not in self.contracts:
            raise ValueError(f"Symbol {symbol} not defined.")

        contract = self.contracts[symbol]

        try:
            # Create the smart depth subscription
            ticker = self.ib.reqMktDepth(contract, numRows=numRows, isSmartDepth=True)
            
            # Store the ticker for cleanup
            self.l2_depth_subs[f"{symbol}_smart"] = ticker

            def on_smart_depth_update(ticker):
                # Process bid side
                for i, bid in enumerate(ticker.domBids):
                    message = MarketDepthMessage(
                        symbol=symbol,
                        position=i,
                        operation=1,
                        side=0,
                        price=bid.price,
                        size=bid.size,
                    )
                    asyncio.create_task(self.queue.put(message))
                
                # Process ask side
                for i, ask in enumerate(ticker.domAsks):
                    message = MarketDepthMessage(
                        symbol=symbol,
                        position=i,
                        operation=1,
                        side=1,
                        price=ask.price,
                        size=ask.size,
                    )
                    asyncio.create_task(self.queue.put(message))

            # Connect to ticker's update event
            ticker.updateEvent += on_smart_depth_update
            
            logger.info(f"Subscribed to smart (L3) market depth for {symbol}")
            
        except Exception as e:
            logger.warning(f"Smart depth not available for {symbol}: {e}")
            # Fallback to regular market depth
            await self.subscribe_order_book(symbol, numRows)

    def normalize_ticker(self, ticker: Ticker) -> dict:
        import math
        
        def safe_float(value):
            """Convert value to float, return None if NaN or invalid"""
            if value is None or (isinstance(value, float) and math.isnan(value)):
                return None
            return float(value) if value is not None else None
    
        return {
            "event_type": "top_of_book",
            "symbol": ticker.contract.symbol if ticker.contract else None,
            "bid": safe_float(ticker.bid),      # ← Now handles NaN
            "ask": safe_float(ticker.ask),      # ← Now handles NaN
            "last": safe_float(ticker.last),    # ← Now handles NaN
            "volume": safe_float(ticker.volume), # ← Now handles NaN
            "timestamp": ticker.time.isoformat() if ticker.time else None,
        }

    async def request_historical_data(
        self, symbol: str, durationStr: str = "1 D", barSizeSetting: str = "1 min", whatToShow: str = "TRADES", useRTH: bool = True
    ) -> None:
        if symbol not in self.contracts:
            raise ValueError(f"Symbol {symbol} not defined.")

        contract = self.contracts[symbol]

        bars = await self.ib.reqHistoricalDataAsync(
            contract,
            endDateTime="",
            durationStr=durationStr,
            barSizeSetting=barSizeSetting,
            whatToShow=whatToShow,
            useRTH=useRTH,
            formatDate=1,
            keepUpToDate=False,
        )

        historical_bars = []
        for bar in bars:
            historical_bars.append(
                HistoricalBar(
                    date=bar.date,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    barCount=getattr(bar, "barCount", None),
                    average=getattr(bar, "average", None),
                )
            )
        response = HistoricalDataResponse(symbol=symbol, bars=historical_bars)
        await self.queue.put(response)

    async def request_fundamental_data(self, symbol: str, reportType: str = "ReportSnapshot") -> None:
        """
        reportType examples: ReportSnapshot, ReportRatios, ReportFinancials, ReportESG, FinRatios, etc.
        """
        if symbol not in self.contracts:
            raise ValueError(f"Symbol {symbol} not defined.")

        contract = self.contracts[symbol]

        data = await self.ib.reqFundamentalDataAsync(contract, reportType)
        response = FundamentalDataResponse(symbol=symbol, report_type=reportType, data=data)
        await self.queue.put(response)

    async def request_fundamental_ratios(self, symbol: str) -> None:
        if symbol not in self.contracts:
            raise ValueError(f"Symbol {symbol} not defined.")

        contract = self.contracts[symbol]

        data = await self.ib.reqFundamentalDataAsync(contract, "FinRatios")
        response = FundamentalRatiosResponse(symbol=symbol, data=data)
        await self.queue.put(response)

    async def run_forever(self) -> None:
        await self.ib.runAsync()

    def current_queue_size(self) -> int:
        return self.queue.qsize()
