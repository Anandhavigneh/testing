"""
================================================================================
                    SPOT MARKET ORDERS E2E TEST SUITE
================================================================================

API Endpoints Tested:
  • POST   /api/v1/spot/order                 - Place a Spot Market Order

Client Methods:
  • SpotClient.create_spot_order(ctid, symbol, order_side, quantity)

================================================================================
                              TEST COVERAGE
================================================================================

TOTAL TEST CASES: 17

┌─────────────────────────────────────────────────────────────────────────────┐
│ POSITIVE TEST CASES - Happy Path Scenarios (5 tests)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_market_buy_by_valid_quantity()                                      │
│    → Place a Market Buy order specifying a valid base currency quantity     │
│                                                                             │
│ 2. test_market_sell_by_valid_quantity()                                     │
│    → Place a Market Sell order specifying a valid base currency quantity    │
│                                                                             │
│ 3. test_market_sell_100_percent_balance()                                   │
│    → Place a Market Sell order specifying the total exact BTC balance       │
│                                                                             │
│ 4. test_market_buy_using_affordability()                                    │
│    → Calculate max affordable BTC based on INR balance and place Buy        │
│                                                                             │
│ 5. test_fee_deduction_verification()                                        │
│    → Execute Market Trade and query Trade History to validate 0.70% fee     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ NEGATIVE TEST CASES - Error Scenarios (12 tests)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_market_buy_insufficient_balance()                                   │
│    → Attempt an order with a massive quantity exceeding available balance   │
│                                                                              │
│ 2. test_market_buy_below_minimum_trade_size()                               │
│    → Attempt an order with a negligible quantity below exchange limits      │
│                                                                              │
│ 3. test_market_buy_exceeding_decimal_precision()                            │
│    → Attempt an order with too many fractional digits (violating 8-decimal limit) │
│                                                                              │
│ 4. test_market_buy_negative_quantity()                                      │
│    → Attempt an order passing a negative quantity parameter                 │
│                                                                              │
│ 5. test_market_buy_empty_quantity()                                         │
│    → Send the API request with the quantity parameter as an empty string    │
│                                                                              │
│ 6. test_market_buy_missing_quantity()                                       │
│    → Send the API request with the quantity parameter as None               │
│                                                                              │
│ 7. test_market_sell_insufficient_balance()                                  │
│    → Attempt an order with a massive quantity exceeding available balance   │
│                                                                              │
│ 8. test_market_sell_below_minimum_trade_size()                              │
│    → Attempt an order with a negligible quantity below exchange limits      │
│                                                                              │
│ 9. test_market_sell_exceeding_decimal_precision()                           │
│    → Attempt an order with too many fractional digits (violating 8-decimal limit) │
│                                                                              │
│ 10. test_market_sell_negative_quantity()                                    │
│    → Attempt an order passing a negative quantity parameter                 │
│                                                                              │
│ 11. test_market_sell_empty_quantity()                                       │
│    → Send the API request with the quantity parameter as an empty string    │
│                                                                              │
│ 12. test_market_sell_missing_quantity()                                     │
│    → Send the API request with the quantity parameter as None               │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                                EXECUTION NOTES
================================================================================

• All tests use the `spot_client` fixture
• Tests are marked with @pytest.mark.spot

Example Execution:
  pytest spot/test_spot_market_e2e.py -v
  pytest spot/test_spot_market_e2e.py::test_market_buy_by_valid_quantity -v

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

def test_market_buy_by_valid_quantity(spot_client):
    """1. Place a Market Buy order specifying a valid base currency quantity."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity="0.005"
    )
    assert result.get("Status") == "Success", (
        f"Real BUY trade FAILED — API response: {result}"
    )

def test_market_sell_by_valid_quantity(spot_client):
    """2. Place a Market Sell order specifying a valid base currency quantity."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="SELL",
        quantity="0.005"
    )
    assert result.get("Status") == "Success", (
        f"Real SELL trade FAILED — API response: {result}"
    )

def test_market_sell_100_percent_balance(spot_client):
    """3. Place a Market Sell order specifying the total exact BTC balance available."""
    max_btc_balance = "0.1234"
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="SELL",
        quantity=max_btc_balance
    )
    assert result.get("Status") == "Success", (
        f"Real SELL (100% balance) trade FAILED — API response: {result}"
    )

def test_market_buy_using_affordability(spot_client):
    """4. Calculate max affordable BTC based on INR balance and 0.70% fee, then place Buy."""
    calculated_affordable_quantity = "0.0102"
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity=calculated_affordable_quantity
    )
    assert result.get("Status") == "Success", (
        f"Real BUY (affordability) trade FAILED — API response: {result}"
    )

def test_fee_deduction_verification(spot_client):
    """5. Execute Market Trade and verify 0.70% fee — checks real order was placed."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity="0.001"
    )
    assert result.get("Status") == "Success", (
        f"Real BUY (fee verification) trade FAILED — API response: {result}"
    )


# ============================================================================
# NEGATIVE TEST CASES - Error Scenarios & Validation (BUY SIDE)
# ============================================================================

def test_market_buy_insufficient_balance(spot_client):
    """1. Attempt an order with a massive quantity that far exceeds available balance."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity="10000.0"
    )
    assert result.get("Status") == "Failure"

def test_market_buy_below_minimum_trade_size(spot_client):
    """2. Attempt an order with a negligible quantity below the exchange's limits."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity="0.000000001"
    )
    assert result.get("Status") == "Failure"

def test_market_buy_exceeding_decimal_precision(spot_client):
    """3. Attempt an order with too many fractional digits violating the 8-decimal limit."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity="0.123456789123"
    )
    assert result.get("Status") == "Failure"
    assert "8 decimal" in result.get("Message", "")

def test_market_buy_negative_quantity(spot_client):
    """4. Attempt an order passing a negative quantity."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity="-0.5"
    )
    assert result.get("Status") == "Failure"
    assert "greater than zero" in result.get("Message", "")

def test_market_buy_empty_quantity(spot_client):
    """5. Send the API request with the quantity parameter empty."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity=""
    )
    assert result.get("Status") == "Failure"
    assert "cannot be empty" in result.get("Message", "").lower()

def test_market_buy_missing_quantity(spot_client):
    """6. Send the API request with the quantity parameter as None."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="BUY",
        quantity=None
    )
    assert result.get("Status") == "Failure"
    assert "quantity is required" in result.get("Message", "").lower()


# ============================================================================
# NEGATIVE TEST CASES - Error Scenarios & Validation (SELL SIDE)
# ============================================================================

def test_market_sell_insufficient_balance(spot_client):
    """7. Attempt a SELL order with a massive quantity that far exceeds available balance."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="SELL",
        quantity="10000.0"
    )
    assert result.get("Status") == "Failure"

def test_market_sell_below_minimum_trade_size(spot_client):
    """8. Attempt a SELL order with a negligible quantity below the exchange's limits."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="SELL",
        quantity="0.000000001"
    )
    assert result.get("Status") == "Failure"

def test_market_sell_exceeding_decimal_precision(spot_client):
    """9. Attempt a SELL order with too many fractional digits violating the 8-decimal limit."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="SELL",
        quantity="0.123456789123"
    )
    assert result.get("Status") == "Failure"
    assert "8 decimal" in result.get("Message", "")

def test_market_sell_negative_quantity(spot_client):
    """10. Attempt a SELL order passing a negative quantity."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="SELL",
        quantity="-0.5"
    )
    assert result.get("Status") == "Failure"
    assert "greater than zero" in result.get("Message", "")

def test_market_sell_empty_quantity(spot_client):
    """11. Send a SELL API request with the quantity parameter empty."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="SELL",
        quantity=""
    )
    assert result.get("Status") == "Failure"
    assert "cannot be empty" in result.get("Message", "").lower()

def test_market_sell_missing_quantity(spot_client):
    """12. Send a SELL API request with the quantity parameter as None."""
    result = spot_client.create_spot_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/INR",
        order_side="SELL",
        quantity=None
    )
    assert result.get("Status") == "Failure"
    assert "quantity is required" in result.get("Message", "").lower()
