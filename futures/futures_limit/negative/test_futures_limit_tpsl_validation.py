"""
================================================================================
                FUTURES TP/SL VALIDATION TEST SUITE
================================================================================

API Endpoints Tested:
  • GET    /api/v1/futures/config
  • GET    /api/v1/futures/ticker
  • POST   /api/v1/futures/order
  • POST   /tpsl/order
  • GET    /api/v1/futures/position
  • GET    /api/v1/futures/view/tpsl

================================================================================
                              TEST COVERAGE
================================================================================

TOTAL TEST CASES: 1

NEGATIVE VALIDATION FLOW:
  • test_futures_limit_long_tpsl_validation()

================================================================================
"""

import time
import pytest
import allure
from config import Config
from clients.futures_trading_client import FuturesTradingClient

pytestmark = pytest.mark.serial

@allure.feature("Futures TP/SL Validation Tests")
@allure.story("Reject Invalid TP/SL on Active Position")
@pytest.mark.serial
def test_futures_limit_long_tpsl_validation():
    client = FuturesTradingClient()
    symbol = "BTC/USDT"

    # ===== PHASE 1: Setup =====
    with allure.step(f"Step 1: Fetch Coin Pair Config for {symbol}"):
        config_resp = client.client.get("config").json()
        assert config_resp.get("Status") == "Success", "Failed to fetch config"
        
        symbol_config = next((s for s in config_resp.get('Data', {}).get('symbol_config', []) if s.get('symbol') == symbol), None)
        assert symbol_config is not None, f"{symbol} config not found"
        min_qty = float(symbol_config['min_qty'])

    with allure.step("Step 2: Fetch Orderbook to get current market price"):
        ticker_resp = client.client.get("ticker").json()
        btc_ticker = ticker_resp.get('Data', {}).get(symbol)
        top_ask = float(btc_ticker['top_ask'])

    # ===== PHASE 2: Place Limit LONG Order =====
    qty_val = min_qty + 0.0001
    qty_str = f"{qty_val:.4f}"
    
    # Place slightly above ask to guarantee immediate fill
    limit_price = top_ask + 5.0
    price_str = f"{limit_price:.1f}"
    amount_str = f"{qty_val * limit_price:.4f}"

    with allure.step("Step 3: Place LIMIT LONG Order to create an active position"):
        order_resp = client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol=symbol,
            qty=qty_str,
            price=price_str,
            amount=amount_str,
            order_type="1",  # LIMIT
            order_side="0",  # LONG / BUY
            leverage="3"
        )
        assert order_resp.get("Status") in ["Success", "100", "200"] or str(order_resp.get("Code")) in ["100", "200"], "Order creation failed"
        time.sleep(2)

    # ===== PHASE 3: Fetch Active Position =====
    with allure.step("Step 4: Fetch Active Position and Verify LONG position exists"):
        pos_resp = client.get_active_positions(ctid=Config.DEFAULT_CTID)
        positions = pos_resp.get("Data", [])
        if isinstance(positions, dict):
            positions = positions.get("list", []) or positions.get("positions", [])
            
        btc_long_positions = [p for p in positions if p.get("symbol") == symbol and p.get("position_side") == "Long"]
        assert len(btc_long_positions) > 0, "No active LONG position found!"
        
        recent_pos = btc_long_positions[0]
        entry_price = float(recent_pos.get("average_entry", recent_pos.get("entry_price", 0)))
        pos_qty_str = str(abs(float(recent_pos.get("qty", recent_pos.get("quantity", "0")))))

    # ===== PHASE 4: Send INVALID TP/SL =====
    with allure.step("Step 5: Send INVALID TP/SL using /tpsl/order endpoint"):
        # For a LONG position:
        # Invalid TP: TP < entry price
        # Invalid SL: SL > entry price
        invalid_tp = entry_price * 0.5
        invalid_sl = entry_price * 1.5
        
        invalid_tp_str = f"{invalid_tp:.1f}"
        invalid_sl_str = f"{invalid_sl:.1f}"
        
        # Test TP validation
        tp_resp = client.update_tpsl_order(
            ctid=Config.DEFAULT_CTID, 
            symbol=symbol, 
            tp_qty=pos_qty_str, 
            tp_price=invalid_tp_str
        )
        
        # Test SL validation
        sl_resp = client.update_tpsl_order(
            ctid=Config.DEFAULT_CTID, 
            symbol=symbol, 
            sl_qty=pos_qty_str, 
            sl_price=invalid_sl_str
        )

    # ===== PHASE 5: Validate API Response =====
    with allure.step("Step 6: Validate API rejected the invalid TP/SL"):
        # The backend should throw an error since the prices are completely invalid
        # TP validation
        assert tp_resp.get("Status") == "Error" or str(tp_resp.get("Code")) != "100", f"TP incorrectly accepted! Resp: {tp_resp}"
        
        # SL validation
        assert sl_resp.get("Status") == "Error" or str(sl_resp.get("Code")) != "100", f"SL incorrectly accepted! Resp: {sl_resp}"

    # ===== PHASE 6: Verify No Wrong TP/SL Applied =====
    with allure.step("Step 7: Verify no invalid TP/SL was applied to the system"):
        view_tpsl_resp = client.view_tpsl_orders(ctid=Config.DEFAULT_CTID, symbol=symbol)
        
        # If the API behaves correctly, it either returns empty list, or none of the invalid targets should be present
        tpsl_data = view_tpsl_resp.get("Data", {})
        tpsl_list = []
        if isinstance(tpsl_data, list):
            tpsl_list = tpsl_data
        elif isinstance(tpsl_data, dict):
            tpsl_list = tpsl_data.get(symbol, [])
            if not tpsl_list:
                tpsl_list = tpsl_data.get("take_profit", []) + tpsl_data.get("stop_loss", [])
                
        for order in tpsl_list:
            order_tp = float(order.get("tp_price", "0"))
            order_sl = float(order.get("sl_price", "0"))
            
            # The exact invalid prices shouldn't be found actively registered in the system
            # Due to precision formatting, we check with a small margin or direct string match
            if order_tp > 0:
                assert abs(order_tp - invalid_tp) > 0.1, f"Found invalid TP {invalid_tp} actively set in the system!"
            if order_sl > 0:
                assert abs(order_sl - invalid_sl) > 0.1, f"Found invalid SL {invalid_sl} actively set in the system!"
