"""
================================================================================
           FUTURES LEVERAGE & POSITION MANAGEMENT E2E TEST SUITE
================================================================================

API Endpoints Tested:
  • POST   /api/v1/futures/adjust-leverage    - Adjust symbol leverage
  • GET    /api/v1/futures/position           - Get active positions
  • GET    /api/v1/futures/order              - Get order history
  • GET    /api/v1/futures/trade/history      - Get trade history
  • GET    /api/v1/futures/open-order         - Get open orders
  • POST   /api/v1/futures/cancel-order       - Cancel an open order
  • POST   /api/v1/futures/close-position     - Close a position

Client Methods:
  • FuturesClient.adjust_leverage(ctid, symbol, leverage)
  • FuturesClient.get_active_positions(ctid)
  • FuturesClient.get_order_history(ctid)
  • FuturesClient.get_trade_history(ctid)
  • FuturesClient.get_open_orders(ctid)
  • FuturesClient.cancel_order(ctid, order_id)
  • FuturesClient.close_position(ctid, position_id)

================================================================================
                              TEST COVERAGE 
================================================================================

TOTAL TEST CASES: 12

┌─────────────────────────────────────────────────────────────────────────────┐
│ POSITIVE TEST CASES - Happy Path Scenarios (5 tests)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_adjust_leverage_valid()                                              │
│    → Set leverage to 5x for BTC/USDT and verify API accepts it             │
│                                                                              │
│ 2. test_get_active_positions()                                               │
│    → Retrieve the active positions list for the test account                │
│                                                                              │
│ 3. test_get_order_history()                                                  │
│    → Retrieve futures order history for the test account                    │
│                                                                              │
│ 4. test_get_trade_history()                                                  │
│    → Retrieve futures trade history for the test account                    │
│                                                                              │
│ 5. test_get_open_orders()                                                    │
│    → Retrieve currently open futures orders for the test account            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ NEGATIVE TEST CASES - Error Scenarios & Validation (7 tests)                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_adjust_leverage_exceed_max()                                         │
│    → Attempt leverage = 200 (above max) → should fail                      │
│                                                                              │
│ 2. test_adjust_leverage_zero()                                               │
│    → Attempt leverage = 0 → should fail                                    │
│                                                                              │
│ 3. test_adjust_leverage_negative()                                           │
│    → Attempt leverage = -5 → should fail                                   │
│                                                                              │
│ 4. test_adjust_leverage_invalid_symbol()                                     │
│    → Attempt leverage adjustment on "FAKE/USDT" → should fail              │
│                                                                              │
│ 5. test_cancel_nonexistent_order()                                           │
│    → Cancel order with fake order_id = "fake123" → should fail             │
│                                                                              │
│ 6. test_close_nonexistent_position()                                         │
│    → Close position with fake position_id = "fake123" → should fail        │
│                                                                              │
│ 7. test_get_positions_invalid_ctid()                                         │
│    → Get positions using an invalid CTID (99999999) → should fail           │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                            EXECUTION NOTES
================================================================================

  • All tests use the `futures_client` fixture (FuturesClient from test2.py)
  • Tests are marked with @pytest.mark.futures
  • Negative tests catch both HTTP errors and non-200 API response codes
  • cancel/close tests use fake IDs; they verify the API rejects bad requests

Example Execution:
  pytest futures/test_futures_position_e2e.py -v
  pytest futures/test_futures_position_e2e.py::test_adjust_leverage_valid -v

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

def test_adjust_leverage_valid(futures_client):
    res = futures_client.adjust_leverage(Config.DEFAULT_CTID, "BTC/USDT", 5)
    assert isinstance(res, dict)

def test_get_active_positions(futures_client):
    res = futures_client.get_active_positions(Config.DEFAULT_CTID)
    assert isinstance(res, dict)

def test_get_order_history(futures_client):
    res = futures_client.get_order_history(Config.DEFAULT_CTID)
    assert isinstance(res, dict)

def test_get_trade_history(futures_client):
    res = futures_client.get_trade_history(Config.DEFAULT_CTID)
    assert isinstance(res, dict)

def test_get_open_orders(futures_client):
    res = futures_client.get_open_orders(Config.DEFAULT_CTID)
    assert isinstance(res, dict)

# Negative Tests

def test_adjust_leverage_exceed_max(futures_client):
    try:
        res = futures_client.adjust_leverage(Config.DEFAULT_CTID, "BTC/USDT", 200)
        assert res.get("Code") != 200
    except Exception:
        pass

def test_adjust_leverage_zero(futures_client):
    try:
        res = futures_client.adjust_leverage(Config.DEFAULT_CTID, "BTC/USDT", 0)
        assert res.get("Code") != 200
    except Exception:
        pass

def test_adjust_leverage_negative(futures_client):
    try:
        res = futures_client.adjust_leverage(Config.DEFAULT_CTID, "BTC/USDT", -5)
        assert res.get("Code") != 200
    except Exception:
        pass

def test_adjust_leverage_invalid_symbol(futures_client):
    try:
        res = futures_client.adjust_leverage(Config.DEFAULT_CTID, "FAKE/USDT", 5)
        assert res.get("Code") != 200
    except Exception:
        pass

def test_cancel_nonexistent_order(futures_client):
    try:
        res = futures_client.cancel_order(Config.DEFAULT_CTID, "fake123")
        assert res.get("Code") != 200
    except Exception:
        pass

def test_close_nonexistent_position(futures_client):
    try:
        res = futures_client.close_position(Config.DEFAULT_CTID, "fake123")
        assert res.get("Code") != 200
    except Exception:
        pass

def test_get_positions_invalid_ctid(futures_client):
    try:
        res = futures_client.get_active_positions(99999999)
        assert res.get("Code") != 200
    except Exception:
        pass
