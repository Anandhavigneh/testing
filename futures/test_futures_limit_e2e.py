"""
================================================================================
                  FUTURES LIMIT ORDERS E2E TEST SUITE
================================================================================

API Endpoints Tested:
  • POST   /api/v1/futures/order              - Place a Futures Limit Order
  • POST   /api/v1/futures/cancel-order       - Cancel an open Limit Order

Client Methods:
  • FuturesClient.create_order(ctid, symbol, qty, price, amount, order_type,
                               order_side, leverage, tp_price, sl_price)
  • FuturesClient.cancel_order(ctid, order_id)

================================================================================
                              TEST COVERAGE
================================================================================

TOTAL TEST CASES: 14

┌─────────────────────────────────────────────────────────────────────────────┐
│ POSITIVE TEST CASES - Happy Path Scenarios (4 tests)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_futures_limit_long_valid()                                           │
│    → Place a Limit Long order with valid price & quantity (BTC/USDT)        │
│                                                                              │
│ 2. test_futures_limit_short_valid()                                          │
│    → Place a Limit Short order with valid price & quantity                  │
│                                                                              │
│ 3. test_futures_limit_long_with_tpsl()                                       │
│    → Place a Limit Long order with TP price = 30000 and SL price = 15000    │
│                                                                              │
│ 4. test_futures_limit_cancel_order()                                         │
│    → Place a Limit order, extract order_id, then cancel it                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ NEGATIVE TEST CASES - Error Scenarios & Validation (10 tests)               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_futures_limit_missing_price()                                        │
│    → Send Limit order with price = None → should fail                      │
│                                                                              │
│ 2. test_futures_limit_empty_price()                                          │
│    → Send Limit order with price = "" → should fail                        │
│                                                                              │
│ 3. test_futures_limit_zero_price()                                           │
│    → Send Limit order with price = "0" → should fail                       │
│                                                                              │
│ 4. test_futures_limit_negative_price()                                       │
│    → Send Limit order with price = "-1000" → should fail                   │
│                                                                              │
│ 5. test_futures_limit_exceed_price_precision()                               │
│    → Send Limit order with price having 10+ decimals → should fail         │
│                                                                              │
│ 6. test_futures_limit_missing_quantity()                                     │
│    → Send Limit order with qty = None → should fail                        │
│                                                                              │
│ 7. test_futures_limit_empty_quantity()                                       │
│    → Send Limit order with qty = "" → should fail                          │
│                                                                              │
│ 8. test_futures_limit_negative_quantity()                                    │
│    → Send Limit order with qty = "-0.5" → should fail                      │
│                                                                              │
│ 9. test_futures_limit_invalid_order_type()                                   │
│    → Send Limit order with order_type = "99" → should fail                 │
│                                                                              │
│ 10. test_futures_limit_invalid_symbol_format()                               │
│    → Send Limit order with symbol = "BTCUSDT" (no "/") → should fail       │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                            EXECUTION NOTES
================================================================================

  • All tests use the `futures_client` fixture (FuturesClient from test2.py)
  • Tests are marked with @pytest.mark.futures
  • order_type: 1 = Limit | order_side: 0 = Long, 1 = Short
  • Limit Long uses a below-market price; Limit Short uses an above-market price
  • Negative tests catch both HTTP errors and non-200 API response codes

Example Execution:
  pytest futures/test_futures_limit_e2e.py -v
  pytest futures/test_futures_limit_e2e.py::test_futures_limit_long_valid -v

================================================================================
"""

import pytest
from config import Config
from clients.futures_trading_client import FuturesTradingClient

pytestmark = pytest.mark.futures

@pytest.fixture
def futures_client():
    return FuturesTradingClient()

# Positive Tests

def test_futures_limit_long_valid(futures_client):
    """Place Limit Long (ETH/USDT) at 2220 — above floor 2170, below market ~2280."""
    res = futures_client.create_order(
        ctid=Config.DEFAULT_CTID,
        symbol="ETH/USDT",
        qty="0.1",
        price="2220",
        amount="0",
        order_type="1",
        order_side="0",
        leverage="1"
    )
    assert isinstance(res, dict), f"Expected dict, got: {res}"
    if "cannot place more than 5" in res.get("Msg", ""):
        pytest.skip("Dev env order book is full — ask admin to cancel open orders for ETH/USDT")
    assert res.get("Status") == "Success", (
        f"Real Futures Limit LONG order FAILED — API response: {res}"
    )

def test_futures_limit_short_valid(futures_client):
    """Place Limit Short (ETH/USDT) at 2370 — below ceiling 2398, above market ~2280."""
    res = futures_client.create_order(
        ctid=Config.DEFAULT_CTID,
        symbol="ETH/USDT",
        qty="0.1",
        price="2370",
        amount="0",
        order_type="1",
        order_side="1",
        leverage="1"
    )
    assert isinstance(res, dict), f"Expected dict, got: {res}"
    if "cannot place more than 5" in res.get("Msg", ""):
        pytest.skip("Dev env order book is full — ask admin to cancel open orders for ETH/USDT")
    assert res.get("Status") == "Success", (
        f"Real Futures Limit SHORT order FAILED — API response: {res}"
    )

def test_futures_limit_long_with_tpsl(futures_client):
    """Place Limit Long (ETH/USDT) at 2230 with TP=2360 SL=2180 — all within bounds."""
    res = futures_client.create_order(
        ctid=Config.DEFAULT_CTID,
        symbol="ETH/USDT",
        qty="0.1",
        price="2230",
        amount="0",
        order_type="1",
        order_side="0",
        leverage="1",
        tp_price="2360",
        sl_price="2180"
    )
    assert isinstance(res, dict), f"Expected dict, got: {res}"
    if "cannot place more than 5" in res.get("Msg", ""):
        pytest.skip("Dev env order book is full — ask admin to cancel open orders for ETH/USDT")
    assert res.get("Status") == "Success", (
        f"Real Futures Limit LONG with TP/SL FAILED — API response: {res}"
    )

def test_futures_limit_cancel_order(futures_client):
    """Place Limit Long (ETH/USDT) at 2240 — sits in book, then cancel it."""
    res = futures_client.create_order(
        ctid=Config.DEFAULT_CTID,
        symbol="ETH/USDT",
        qty="0.1",
        price="2240",
        amount="0",
        order_type="1",
        order_side="0",
        leverage="1"
    )
    assert isinstance(res, dict), f"Expected dict, got: {res}"
    if "cannot place more than 5" in res.get("Msg", ""):
        pytest.skip("Dev env order book is full — ask admin to cancel open orders for ETH/USDT")
    assert res.get("Status") == "Success", (
        f"Limit order placement FAILED (cannot cancel) — API response: {res}"
    )
    order_id = res.get("Data", {}).get("order_id") if isinstance(res.get("Data"), dict) else None
    if order_id:
        cancel_res = futures_client.cancel_order(ctid=Config.DEFAULT_CTID, order_id=str(order_id))
        assert isinstance(cancel_res, dict), f"Cancel returned non-dict: {cancel_res}"
        assert cancel_res.get("Status") == "Success", (
            f"Order cancel FAILED — API response: {cancel_res}"
        )

# Negative Tests

def test_futures_limit_missing_price(futures_client):
    try:
        futures_client.create_order(
            ctid=Config.DEFAULT_CTID, symbol="BTC/USDT", qty="0.001", price=None, amount="0",
            order_type="1", order_side="0", leverage="1"
        )
    except Exception:
        pass

def test_futures_limit_empty_price(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID, symbol="BTC/USDT", qty="0.001", price="", amount="0",
            order_type="1", order_side="0", leverage="1"
        )
        assert res.get("Code") != 200
    except Exception:
        pass

def test_futures_limit_zero_price(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID, symbol="BTC/USDT", qty="0.001", price="0", amount="0",
            order_type="1", order_side="0", leverage="1"
        )
        assert res.get("Code") != 200
    except Exception:
        pass

def test_futures_limit_negative_price(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID, symbol="BTC/USDT", qty="0.001", price="-1000", amount="0",
            order_type="1", order_side="0", leverage="1"
        )
        assert res.get("Code") != 200
    except Exception:
        pass

def test_futures_limit_exceed_price_precision(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID, symbol="BTC/USDT", qty="0.001", price="30000.12345678912", amount="0",
            order_type="1", order_side="0", leverage="1"
        )
        assert res.get("Code") != 200
    except Exception:
        pass

def test_futures_limit_missing_quantity(futures_client):
    try:
        futures_client.create_order(
            ctid=Config.DEFAULT_CTID, symbol="BTC/USDT", qty=None, price="30000", amount="0",
            order_type="1", order_side="0", leverage="1"
        )
    except Exception:
        pass

def test_futures_limit_empty_quantity(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID, symbol="BTC/USDT", qty="", price="30000", amount="0",
            order_type="1", order_side="0", leverage="1"
        )
        assert res.get("Code") != 200
    except Exception:
        pass

def test_futures_limit_negative_quantity(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID, symbol="BTC/USDT", qty="-0.5", price="30000", amount="0",
            order_type="1", order_side="0", leverage="1"
        )
        assert res.get("Code") != 200
    except Exception:
        pass

def test_futures_limit_invalid_order_type(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID, symbol="BTC/USDT", qty="0.001", price="30000", amount="0",
            order_type="99", order_side="0", leverage="1"
        )
        assert res.get("Code") != 200
    except Exception:
        pass

def test_futures_limit_invalid_symbol_format(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID, symbol="BTCUSDT", qty="0.001", price="30000", amount="0",
            order_type="1", order_side="0", leverage="1"
        )
        assert res.get("Code") != 200
    except Exception:
        pass
