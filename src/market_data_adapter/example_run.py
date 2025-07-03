import asyncio
from market_data_adapter import MarketDataAdapter


async def main():
    adapter = MarketDataAdapter()
    await adapter.connect()

    adapter.define_contracts(["PLTR"])

    # Subscribe to top-of-book
    await adapter.subscribe_top_of_book("PLTR")

    # Subscribe to tick-by-tick trades
    await adapter.subscribe_tick_by_tick("PLTR", tickType="Last")

    # Subscribe to L2 market depth
    await adapter.subscribe_order_book("PLTR")

    # Subscribe to L3 (smart) market depth
    await adapter.subscribe_smart_depth("PLTR")

    # Request historical data (1 day, 1-min bars)
    await adapter.request_historical_data("PLTR", durationStr="1 D", barSizeSetting="1 min")

    # Request fundamental data (snapshot)
    await adapter.request_fundamental_data("PLTR", reportType="ReportSnapshot")

    # Request fundamental ratios
    await adapter.request_fundamental_ratios("PLTR")

    # Collect messages for 10 seconds
    try:
        for _ in range(100):
            msg = await asyncio.wait_for(adapter.queue.get(), timeout=10)
            print(msg)
    except asyncio.TimeoutError:
        print("No more messages received in 10 seconds.")

    await adapter.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
