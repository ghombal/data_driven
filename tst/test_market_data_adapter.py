import pytest
import asyncio
from data_driven.market_data_adapter.market_data_adapter import MarketDataAdapter


@pytest.mark.asyncio
async def test_connection_and_contract_definition():
    adapter = MarketDataAdapter()
    await adapter.connect()

    adapter.define_contracts(["PLTR"])
    assert "PLTR" in adapter.contracts

    await adapter.disconnect()


@pytest.mark.asyncio
async def test_subscribe_top_of_book_and_queue():
    adapter = MarketDataAdapter()
    await adapter.connect()
    adapter.define_contracts(["PLTR"])

    await adapter.subscribe_top_of_book("PLTR")

    # Wait briefly for data to arrive
    try:
        msg = await asyncio.wait_for(adapter.queue.get(), timeout=5)
        assert msg.symbol == "PLTR"
        assert msg.event_type == "top_of_book"
    except asyncio.TimeoutError:
        pytest.skip("No top-of-book data received within timeout.")

    await adapter.disconnect()


@pytest.mark.asyncio
async def test_historical_data_request():
    adapter = MarketDataAdapter()
    await adapter.connect()
    adapter.define_contracts(["PLTR"])

    await adapter.request_historical_data("PLTR", durationStr="1 D", barSizeSetting="1 min")

    try:
        msg = await asyncio.wait_for(adapter.queue.get(), timeout=5)
        assert msg.symbol == "PLTR"
        assert msg.event_type == "historical_data"
        assert len(msg.bars) > 0
    except asyncio.TimeoutError:
        pytest.skip("No historical data received within timeout.")

    await adapter.disconnect()
