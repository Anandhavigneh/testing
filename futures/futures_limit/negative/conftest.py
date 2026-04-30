import pytest
from clients.futures_trading_client import FuturesTradingClient

@pytest.fixture(scope="module")
def setup_data():
    """Fetch ticker data once to get valid base values for the negative tests."""
    client = FuturesTradingClient()
    ticker_resp = client.client.get("ticker").json()
    eth_ticker = ticker_resp.get("Data", {}).get("ETH/USDT", {})
    top_ask = float(eth_ticker.get("top_ask", "2000.0"))
    
    return {
        "client": client,
        "symbol": "ETH/USDT",
        "valid_qty": "0.015",
        "valid_price": str(round(top_ask - 100, 2)),
        "valid_amount": str(round(0.015 * (top_ask - 100), 4)),
        "top_ask": top_ask
    }
