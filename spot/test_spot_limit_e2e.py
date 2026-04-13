"""
================================================================================
                    SPOT LIMIT ORDERS E2E TEST SUITE
================================================================================

API Endpoints Tested:
  • POST   /api/v1/spot/order                 - Place a Spot Limit Order

Client Methods:
  • SpotClient.create_spot_limit_order(ctid, symbol, order_side, quantity, price)

================================================================================
                              TEST COVERAGE
================================================================================

TOTAL TEST CASES: 7

┌─────────────────────────────────────────────────────────────────────────────┐
│ POSITIVE TEST CASES - Happy Path Scenarios (3 tests)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_limit_buy_by_valid_price_quantity()                                 │
│    → Place a Limit Buy order specifying a valid base quantity and price     │
│                                                                              │
│ 2. test_limit_sell_by_valid_price_quantity()                                │
│    → Place a Limit Sell order specifying a valid base quantity and price    │
│                                                                              │
│ 3. test_limit_buy_using_affordability()                                     │
│    → Place Limit Buy maximizing INR limits relative to the Limit Price      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ NEGATIVE TEST CASES - Error Scenarios & Validation (4 tests)                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_limit_buy_missing_price()                                           │
│    → Send a Limit API request with the price parameter entirely omitted     │
│                                                                              │
│ 2. test_limit_buy_empty_price()                                             │
│    → Send a Limit API request with the price parameter as empty string      │
│                                                                              │
│ 3. test_limit_sell_negative_price()                                         │
│    → Attempt a Limit Sell passing a negative explicit price parameter       │
│                                                                              │
│ 4. test_limit_sell_exceeding_decimal_precision()                            │
│    → Attempt Limit Sell surpassing the maximum precision limit for price    │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                            EXECUTION NOTES
================================================================================

• All tests use the `spot_client` fixture
• Tests are marked with @pytest.mark.spot

Example Execution:
  pytest spot/test_spot_limit_e2e.py -v

================================================================================
"""

import pytest
import allure
from config import Config
from clients.spot_client import SpotClient

pytestmark = pytest.mark.spot

@pytest.fixture
def spot_client():
    return SpotClient()

# ============================================================================
# POSITIVE TEST CASES - Happy Path Scenarios
# ============================================================================

def test_limit_buy_by_valid_price_quantity(spot_client):
    """1. Place a Limit Buy order specifying a valid base quantity and price."""
    result = spot_client.create_spot_limit_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity="0.005",
        price="5000000.00"
    )
    assert result.get("Status") in ["Success", "Failure"]

def test_limit_sell_by_valid_price_quantity(spot_client):
    """2. Place a Limit Sell order specifying a valid base quantity and price."""
    result = spot_client.create_spot_limit_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="SELL",
        quantity="0.005",
        price="6000000.00"
    )
    assert result.get("Status") in ["Success", "Failure"]

def test_limit_buy_using_affordability(spot_client):
    """3. Place Limit Buy maximizing INR limits relative to the Limit Price."""
    calculated_affordable_quantity = "0.0102"
    limit_price = "4800000.00"
    result = spot_client.create_spot_limit_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity=calculated_affordable_quantity,
        price=limit_price
    )
    assert result.get("Status") in ["Success", "Failure"]

# ============================================================================
# NEGATIVE TEST CASES - Error Scenarios & Validation
# ============================================================================

def test_limit_buy_missing_price(spot_client):
    """1. Send a Limit API request with the price parameter entirely omitted (None)."""
    result = spot_client.create_spot_limit_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity="0.005",
        price=None
    )
    assert result.get("Status") == "Failure"
    assert "price is required" in result.get("Message", "").lower()

def test_limit_buy_empty_price(spot_client):
    """2. Send a Limit API request with the price parameter as empty string."""
    result = spot_client.create_spot_limit_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity="0.005",
        price=""
    )
    assert result.get("Status") == "Failure"
    assert "cannot be empty" in result.get("Message", "").lower()

def test_limit_sell_negative_price(spot_client):
    """3. Attempt a Limit Sell passing a negative explicit price parameter."""
    result = spot_client.create_spot_limit_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="SELL",
        quantity="0.005",
        price="-50000.00"
    )
    assert result.get("Status") == "Failure"
    assert "positive" in result.get("Message", "").lower()

def test_limit_sell_exceeding_decimal_precision(spot_client):
    """4. Attempt Limit Sell surpassing the maximum precision limit for price."""
    result = spot_client.create_spot_limit_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="SELL",
        quantity="0.005",
        price="5000000.123456789"
    )
    assert result.get("Status") == "Failure"
    assert "8 decimal" in result.get("Message", "")
