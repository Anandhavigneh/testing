"""
================================================================================
        FUTURES LIMIT E2E TEST SUITE - SHORT REDUCE
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
│ • test_futures_limit_short_reduce                                            │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                            EXECUTION NOTES
================================================================================

• All tests must use @pytest.mark.serial
• Safe for parallel execution with pytest-xdist

Example Execution:
  pytest futures_limit/positive/test_futures_limit_short_reduce.py -v
  pytest futures_limit/positive/test_futures_limit_short_reduce.py --alluredir=allure-results

================================================================================
"""

import time
import pytest
import allure
from config import Config
from clients.futures_trading_client import FuturesTradingClient

pytestmark = pytest.mark.serial

@allure.feature("Futures E2E Flow")
@allure.story("Futures Limit Orders: Take Short Trade and Apply 50% Reduce-Only Position")
@pytest.mark.serial
def test_futures_limit_short_reduce():
    """
    Test complete flow: Create a Short limit order (with size big enough to reduce),
    verify the position, attach TP/SL, and then execute a 50% reduce-only long order.
    Verify that the position size decreases and no opposing long position is opened.
    """
    futures_client = FuturesTradingClient()
    symbol = "ETH/USDT"
    target_leverage = 5
    leverage_str = str(target_leverage)

    # ===== PHASE 1: Setup =====
    with allure.step(f"Step 1: Fetch Coin Pair Config and Validate Required Fields for {symbol}"):
        config_resp = futures_client.client.get("config").json()
        assert config_resp.get("Status") == "Success", f"Failed to fetch config: {config_resp}"
        
        symbol_config = next((s for s in config_resp.get('Data', {}).get('symbol_config', []) if s.get('symbol') == symbol), None)
        assert symbol_config is not None, f"{symbol} config not found"
        
        min_qty = float(symbol_config['min_qty'])
        max_leverage = symbol_config['leverage']['max_leverage_short']
        assert min_qty > 0, "Invalid min_qty"
        assert max_leverage >= target_leverage, f"Required leverage {target_leverage}X not supported"

    with allure.step("Step 2: Fetch Order Book and Get Current Bid Price"):
        ticker_resp = futures_client.client.get("ticker").json()
        assert ticker_resp.get("Status") == "Success", f"Failed to fetch ticker: {ticker_resp}"
        
        eth_ticker = ticker_resp.get('Data', {}).get(symbol)
        assert eth_ticker is not None, f"{symbol} ticker not found"
        
        top_bid = float(eth_ticker['top_bid'])
        assert top_bid > 0, "Top bid price should be greater than 0"

    # ===== PHASE 2: Adjust Leverage =====
    with allure.step(f"Step 3: Adjust Leverage to {target_leverage}X before placing order"):
        leverage_resp = futures_client.adjust_leverage(
            ctid=Config.DEFAULT_CTID,
            symbol=symbol,
            leverage=target_leverage
        )
        is_success = leverage_resp.get("Status") in ["Success", "100", "200"] or str(leverage_resp.get("Code")) in ["100", "200"]
        is_disabled = "disabled" in str(leverage_resp.get("Msg", "")).lower()
        assert is_success or is_disabled, f"Failed to adjust leverage: {leverage_resp}"

    # ===== PHASE 3: Entry (Full Size) =====
    # We must ensure the initial qty is large enough so that 50% of it is >= min_qty.
    initial_qty_val = min_qty * 3.0
    # ETH/USDT has a max precision of 3 decimal places for quantity
    qty_str = f"{initial_qty_val:.3f}"
    
    # Limit Price < Bid guarantees immediate fill for Short entry
    limit_price = top_bid - 5.0
    price_str = f"{limit_price:.1f}"
    amount_str = f"{initial_qty_val * limit_price:.4f}"

    with allure.step(f"Step 4: Frame Payload and Take Trade (Short Limit Order) for qty {qty_str}"):
        order_resp = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol=symbol,
            qty=qty_str,
            price=price_str,
            amount=amount_str,
            order_type="1",  # 1 = LIMIT
            order_side="1",  # 1 = SHORT / SELL
            leverage=leverage_str
        )
        assert isinstance(order_resp, dict)
        assert order_resp.get("Status") in ["Success", "100", "200"] or str(order_resp.get("Code")) in ["100", "200"], f"Order failed: {order_resp}"

    with allure.step("Step 5: Wait for Initial Order Execution"):
        time.sleep(2)

    # ===== PHASE 4: Position Validation =====
    with allure.step("Step 6: Verify Active Position Opened"):
        pos_resp = futures_client.get_active_positions(ctid=Config.DEFAULT_CTID)
        assert pos_resp.get("Status") == "Success" or str(pos_resp.get("Code")) in ["100", "200"], f"Failed to fetch positions: {pos_resp}"
        positions = pos_resp.get("Data", [])
        
        eth_short_positions = [p for p in (positions if isinstance(positions, list) else (positions.get("list", []) or positions.get("positions", []))) if p.get("symbol") == symbol and p.get("position_side") == "Short"]
        assert len(eth_short_positions) > 0, f"{symbol} SHORT position not found in active positions."
        recent_pos = eth_short_positions[0]

        entry_price = float(recent_pos.get("average_entry", recent_pos.get("entry_price", 0)))
        pos_qty_str = recent_pos.get("qty", recent_pos.get("quantity", "0"))
        pos_qty_float = abs(float(pos_qty_str))  # Use absolute value for short calculations
        assert pos_qty_float > 0, f"Position quantity is not greater than 0: {pos_qty_str}"
        assert entry_price > 0, "Entry price is invalid / 0"
        
        abs_qty_str = str(pos_qty_float)

    # ===== PHASE 5: Place TP/SL =====
    with allure.step("Step 7: Place TP / SL on Active Position"):
        # For SHORT, TP is below entry, SL is above entry (5% rule)
        tp_price_val = entry_price * 0.95
        sl_price_val = entry_price * 1.05
        tp_str = f"{tp_price_val:.1f}"
        sl_str = f"{sl_price_val:.1f}"

        tp_resp = futures_client.update_tpsl_order(ctid=Config.DEFAULT_CTID, symbol=symbol, tp_qty=abs_qty_str, tp_price=tp_str)
        assert tp_resp.get("Status") == "Success" or str(tp_resp.get("Code")) in ["100", "200"], f"Failed to place TP: {tp_resp}"

        sl_resp = futures_client.update_tpsl_order(ctid=Config.DEFAULT_CTID, symbol=symbol, sl_qty=abs_qty_str, sl_price=sl_str)
        assert sl_resp.get("Status") == "Success" or str(sl_resp.get("Code")) in ["100", "200"], f"Failed to place SL: {sl_resp}"

    with allure.step("Step 8: Wait for TP/SL Processing"):
        time.sleep(2)

    # ===== PHASE 6: Reduce Position (50%) =====
    with allure.step("Step 9: Place Reduce-Only LONG Limit Order (50% of position)"):
        ticker_resp = futures_client.client.get("ticker").json()
        top_ask = float(ticker_resp.get('Data', {}).get(symbol)['top_ask'])
        
        # Calculate 50% of current absolute position quantity
        reduce_qty_val = pos_qty_float * 0.50
        reduce_qty_str = f"{reduce_qty_val:.3f}"
        
        # We place a LONG limit order slightly above the ask to guarantee immediate execution.
        reduce_price = top_ask + 5.0
        reduce_price_str = f"{reduce_price:.1f}"
        reduce_amount_str = f"{reduce_qty_val * reduce_price:.4f}"
        
        reduce_resp = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol=symbol,
            qty=reduce_qty_str,
            price=reduce_price_str,
            amount=reduce_amount_str,
            order_type="1",  # LIMIT
            order_side="0",  # LONG / BUY (opposite of SHORT position)
            leverage=leverage_str,
            reduce_only="1"  # IMPORTANT ⚠️ True
        )
        assert reduce_resp.get("Status") in ["Success", "100", "200"] or str(reduce_resp.get("Code")) in ["100", "200"], f"Reduce order failed: {reduce_resp}"

    with allure.step("Step 10: Wait for Reduce Order Execution"):
        time.sleep(2)

    # ===== PHASE 7: Verify Reduce Behavior =====
    with allure.step("Step 11: Verify Quantity Reduced and No Opposite Position Created"):
        final_pos_resp = futures_client.get_active_positions(ctid=Config.DEFAULT_CTID)
        final_positions = final_pos_resp.get("Data", [])
        if isinstance(final_positions, dict):
            final_positions = final_positions.get("list", []) or final_positions.get("positions", [])
            
        final_longs = [p for p in final_positions if p.get("symbol") == symbol and p.get("position_side") == "Long"]
        final_shorts = [p for p in final_positions if p.get("symbol") == symbol and p.get("position_side") == "Short"]
        
        # 1. No new LONG position created (reduceOnly successfully prevented opposite exposure)
        assert len(final_longs) == 0, f"FAILED: New LONG position was opened incorrectly! {final_longs}"
        
        # 2. Position still SHORT
        assert len(final_shorts) > 0, "FAILED: SHORT position disappeared entirely!"
        
        # 3. Quantity reduced correctly
        final_short = final_shorts[0]
        final_qty_float = abs(float(final_short.get("qty", final_short.get("quantity", "0"))))
        
        expected_final_qty = pos_qty_float - float(reduce_qty_str)
        # Verify the final quantity is within a small floating point tolerance of expected
        assert abs(final_qty_float - expected_final_qty) < 0.0001, f"FAILED: Quantity mismatch! Expected ~{expected_final_qty}, got {final_qty_float}"
