"""
================================================================================
        FUTURES LIMIT E2E TEST SUITE - LONG LIMIT ORDER
================================================================================

API Endpoints Tested:
  • GET    /api/v1/futures/config             - Get Config
  • GET    /api/v1/futures/ticker             - Get Order Book / Ticker
  • POST   /api/v1/futures/order              - Place Limit Order
  • GET    /api/v1/futures/position           - Get Active Positions

Client Methods:
  • FuturesTradingClient.client.get("config")
  • FuturesTradingClient.client.get("ticker")
  • FuturesTradingClient.create_order(...)
  • FuturesTradingClient.get_active_positions(...)

================================================================================
                              TEST COVERAGE
================================================================================

TOTAL TEST CASES: 1

┌─────────────────────────────────────────────────────────────────────────────┐
│ MAIN FLOW TESTS                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ • test_futures_limit_long_active_position                                    │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                            EXECUTION NOTES
================================================================================

• All tests must use @pytest.mark.serial
• Safe for parallel execution with pytest-xdist

Example Execution:
  pytest futures_limit/positive/test_futures_limit_long.py -v
  pytest futures_limit/positive/test_futures_limit_long.py --alluredir=allure-results

================================================================================
"""

import time
import pytest
import allure
from config import Config
from clients.futures_trading_client import FuturesTradingClient

# Marker for tests that modify shared user preferences and must run serially
pytestmark = pytest.mark.serial

@allure.feature("Futures E2E Flow")
@allure.story("Futures Limit Orders: Place Long Limit Order and Verify Active Position")
@pytest.mark.serial
def test_futures_limit_long_active_position():
    """
    Test complete flow: Fetch configuration, resolve ticker price, and place a long limit order 
    that immediately fills. Validates the active position creation and correctness.
    """
    futures_client = FuturesTradingClient()
    symbol = "BTC/USDT"
    
    # ===== PHASE 1: Setup =====
    with allure.step(f"Step 1: Fetch Coin Pair Config and Validate Required Fields for {symbol}"):
        config_resp = futures_client.client.get("config").json()
        assert config_resp.get("Status") == "Success", f"Failed to fetch config: {config_resp}"
        
        symbol_config = next((s for s in config_resp.get('Data', {}).get('symbol_config', []) if s.get('symbol') == symbol), None)
        assert symbol_config is not None, f"{symbol} config not found"
        
        min_qty = float(symbol_config['min_qty'])
        max_leverage = symbol_config['leverage']['max_leverage_long']
        assert min_qty > 0, "Invalid min_qty"
        assert max_leverage >= 3, "Required leverage not supported"

    with allure.step("Step 2: Fetch Order Book and Get Current Ask Price"):
        ticker_resp = futures_client.client.get("ticker").json()
        assert ticker_resp.get("Status") == "Success", f"Failed to fetch ticker: {ticker_resp}"
        
        btc_ticker = ticker_resp.get('Data', {}).get(symbol)
        assert btc_ticker is not None, f"{symbol} ticker not found"
        
        top_ask = float(btc_ticker['top_ask'])
        assert top_ask > 0, "Top ask price should be greater than 0"

    # ===== PHASE 2: Action =====
    with allure.step("Step 3: Frame Payload and Place Long Limit Order"):
        # A long limit order executes immediately if price >= ask
        qty_val = min_qty + 0.0001
        qty_str = f"{qty_val:.4f}"
        limit_price = top_ask + 5.0
        price_str = f"{limit_price:.1f}"
        amount_str = f"{qty_val * limit_price:.4f}"
        leverage_val = "3"

        order_resp = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol=symbol,
            qty=qty_str,
            price=price_str,
            amount=amount_str,
            order_type="1",  # 1 = LIMIT
            order_side="0",  # 0 = LONG / BUY
            leverage=leverage_val
        )
        
        assert isinstance(order_resp, dict)
        assert order_resp.get("Status") in ["Success", "100", "200"] or str(order_resp.get("Code")) in ["100", "200"], f"Order failed: {order_resp}"

    with allure.step("Step 4: Wait for Order Processing"):
        # Allow system time to process and create the active position
        time.sleep(2)

    # ===== PHASE 3: Validation =====
    with allure.step("Step 5: Fetch Open Positions and Verify Position Details"):
        pos_resp = futures_client.get_active_positions(ctid=Config.DEFAULT_CTID)
        assert pos_resp.get("Status") == "Success" or str(pos_resp.get("Code")) in ["100", "200"], f"Failed to fetch positions: {pos_resp}"
        
        positions = pos_resp.get("Data", [])
        
        btc_long_positions = []
        if isinstance(positions, list):
            for p in positions:
                if p.get("symbol") == symbol and p.get("position_side") == "Long": 
                    btc_long_positions.append(p)
        elif isinstance(positions, dict):
            pos_list = positions.get("list", []) or positions.get("positions", [])
            for p in pos_list:
                if p.get("symbol") == symbol and p.get("position_side") == "Long":
                    btc_long_positions.append(p)
                    
        assert len(btc_long_positions) > 0, f"{symbol} LONG position not found in active positions."
        
        recent_pos = btc_long_positions[0]
        
        # Validate business logic and final state
        assert recent_pos.get("symbol") == symbol, "Symbol mismatch in active position"
        
        pos_qty = float(recent_pos.get("qty", recent_pos.get("quantity", 0)))
        assert pos_qty > 0, f"Position quantity is not greater than 0: {pos_qty}"
        
        entry_price = float(recent_pos.get("average_entry", recent_pos.get("entry_price", 0)))
        assert entry_price > 0, "Entry price is invalid / 0"
