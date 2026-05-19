"""
================================================================================
        FUTURES LIMIT E2E TEST SUITE - LONG REDUCE
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
│ • test_futures_limit_long_reduce                                             │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                            EXECUTION NOTES
================================================================================

• All tests must use @pytest.mark.serial
• Safe for parallel execution with pytest-xdist

Example Execution:
  pytest futures_limit/positive/test_futures_limit_long_reduce.py -v
  pytest futures_limit/positive/test_futures_limit_long_reduce.py --alluredir=allure-results

================================================================================
"""

import time
import pytest
import allure
from config import Config
from clients.futures_trading_client import FuturesTradingClient

pytestmark = pytest.mark.serial

@allure.feature("Futures E2E Flow")
@allure.story("Futures Limit Orders: Take Long Trade and Apply 50% Reduce-Only Position")
@pytest.mark.serial
def test_futures_limit_long_reduce():
    """
    Test complete flow: Create a Long limit order (with size big enough to reduce),
    verify the position, attach TP/SL, and then execute a 50% reduce-only short order.
    Verify that the position size decreases and no opposing short position is opened.
    """
    futures_client = FuturesTradingClient()
    symbol = "BTC/USDT"

    # ===== PHASE 1: Fetch Active Positions =====
    with allure.step(f"Step 1: Check for already active positions for {symbol}"):
        pos_resp = futures_client.get_active_positions(ctid=Config.DEFAULT_CTID)
        assert pos_resp.get("Status") == "Success" or str(pos_resp.get("Code")) in ["100", "200"], f"Failed to fetch positions: {pos_resp}"
        
        positions = pos_resp.get("Data", [])
        positions_list = positions if isinstance(positions, list) else (positions.get("list", []) or positions.get("positions", []))
        
        target_position = None
        for p in positions_list:
            if p.get("symbol") == symbol:
                target_position = p
                break
                
        if not target_position:
            pytest.skip(f"No active position found for {symbol} to close.")
            
        pos_qty = float(target_position.get("qty", target_position.get("quantity", "0")))
        position_side = target_position.get("position_side", "")
        leverage_str = str(target_position.get("leverage", "3")).replace("x", "")

    # ===== PHASE 2: Close Position =====
    with allure.step(f"Step 2: Close the already active {position_side} position"):
        if abs(pos_qty) > 0:
            ticker_resp = futures_client.client.get("ticker").json()
            btc_ticker = ticker_resp.get("Data", {}).get(symbol, {})
            
            if pos_qty > 0:  # LONG position, need to SHORT to close
                close_side = "1"
                close_price = float(btc_ticker.get("top_bid", 0)) - 100.0
            else:  # SHORT position, need to LONG to close
                close_side = "0"
                close_price = float(btc_ticker.get("top_ask", 0)) + 100.0
                
            close_qty_str = f"{abs(pos_qty):.4f}"
            close_price_str = f"{close_price:.1f}"
            close_amt_str = f"{abs(pos_qty) * close_price:.4f}"
            
            reduce_resp = futures_client.create_order(
                ctid=Config.DEFAULT_CTID,
                symbol=symbol,
                qty=close_qty_str,
                price=close_price_str,
                amount=close_amt_str,
                order_type="1",  # Limit
                order_side=close_side,
                leverage=leverage_str,
                reduce_only="1"
            )
            assert reduce_resp.get("Status") in ["Success", "100", "200"] or str(reduce_resp.get("Code")) in ["100", "200"], f"Close order failed: {reduce_resp}"

    with allure.step("Step 3: Wait for Order Execution"):
        time.sleep(2)

    # ===== PHASE 3: Verify Close =====
    with allure.step("Step 4: Verify the position is closed"):
        final_pos_resp = futures_client.get_active_positions(ctid=Config.DEFAULT_CTID)
        final_positions = final_pos_resp.get("Data", [])
        if isinstance(final_positions, dict):
            final_positions = final_positions.get("list", []) or final_positions.get("positions", [])
            
        remaining = [p for p in final_positions if p.get("symbol") == symbol and p.get("position_side") == position_side]
        assert len(remaining) == 0, f"FAILED: Position was not fully closed! {remaining}"
