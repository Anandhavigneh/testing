"""
================================================================================
        FUTURES LIMIT E2E TEST SUITE - LONG TP/SL
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
│ • test_futures_limit_long_with_tpsl                                          │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                            EXECUTION NOTES
================================================================================

• All tests must use @pytest.mark.serial
• Safe for parallel execution with pytest-xdist

Example Execution:
  pytest futures_limit/positive/test_futures_limit_long_tpsl.py -v
  pytest futures_limit/positive/test_futures_limit_long_tpsl.py --alluredir=allure-results

================================================================================
"""

import time
import pytest
import allure
from config import Config
from clients.futures_trading_client import FuturesTradingClient

pytestmark = pytest.mark.serial

@allure.feature("Futures E2E Flow")
@allure.story("Futures Limit Orders: Take Trade and Place TP/SL on Active Position")
@pytest.mark.serial
def test_futures_limit_long_with_tpsl():
    """
    Test complete flow: Fetch config, place a limit order that fills immediately,
    verify the active position, and THEN apply TP/SL targets specifically to that 
    position and verify they were successfully opened in the system.
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

    # ===== PHASE 2: Entry =====
    qty_val = min_qty + 0.0001
    qty_str = f"{qty_val:.4f}"
    
    # Limit Price > Ask guarantees immediate fill
    limit_price = top_ask + 5.0
    price_str = f"{limit_price:.1f}"
    amount_str = f"{qty_val * limit_price:.4f}"
    leverage_val = "3"

    with allure.step("Step 3: Frame Payload and Take Trade (Long Limit Order)"):
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

    with allure.step("Step 4: Wait for Order Execution"):
        time.sleep(2)

    # ===== PHASE 3: Position Validation =====
    with allure.step("Step 5: Verify Active Position Opened"):
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

        entry_price = float(recent_pos.get("average_entry", recent_pos.get("entry_price", 0)))
        pos_qty_str = recent_pos.get("qty", recent_pos.get("quantity", "0"))
        assert entry_price > 0, "Entry price is invalid / 0"
        
    # ===== PHASE 4: Place TP/SL =====
    with allure.step("Step 6: Place TP / SL on Active Position"):
        # Calculate TP and SL based on the actual entry price!
        # Giottus requires SL to be at least ~3% below entry for LONG.
        tp_price_val = entry_price * 1.05  # TP 5% > Entry
        sl_price_val = entry_price * 0.95  # SL 5% < Entry
        tp_str = f"{tp_price_val:.1f}"
        sl_str = f"{sl_price_val:.1f}"

        # Due to API constraint where placing 100% TP and SL in a single call fails,
        # we apply them via two separate calls.
        tp_resp = futures_client.update_tpsl_order(
            ctid=Config.DEFAULT_CTID,
            symbol=symbol,
            tp_qty=pos_qty_str,
            tp_price=tp_str
        )
        assert tp_resp.get("Status") == "Success" or str(tp_resp.get("Code")) in ["100", "200"], f"Failed to place TP: {tp_resp}"

        sl_resp = futures_client.update_tpsl_order(
            ctid=Config.DEFAULT_CTID,
            symbol=symbol,
            sl_qty=pos_qty_str,
            sl_price=sl_str
        )
        assert sl_resp.get("Status") == "Success" or str(sl_resp.get("Code")) in ["100", "200"], f"Failed to place SL: {sl_resp}"

    with allure.step("Step 7: Wait for TP/SL Processing"):
        time.sleep(2)

    # ===== PHASE 5: Verify TP/SL Targets =====
    with allure.step("Step 8: Fetch and Verify Open TP/SL Targets"):
        view_tpsl_resp = futures_client.view_tpsl_orders(ctid=Config.DEFAULT_CTID, symbol=symbol)
        assert view_tpsl_resp.get("Status") == "Success", f"Failed to fetch TP/SL view: {view_tpsl_resp}"
        
        tpsl_data = view_tpsl_resp.get("Data", {})
        
        # The TPSL response often groups orders by symbol
        tpsl_list = []
        if isinstance(tpsl_data, list):
            tpsl_list = tpsl_data
        elif isinstance(tpsl_data, dict):
            tpsl_list = tpsl_data.get(symbol, [])
            if not tpsl_list:
                # Flat list might be directly under 'take_profit' or 'stop_loss' in some cases
                tpsl_list = tpsl_data.get("take_profit", []) + tpsl_data.get("stop_loss", [])
                
        tp_orders = []
        sl_orders = []
        
        for order in tpsl_list:
            order_type = str(order.get("order_type_num", order.get("order_type", ""))).lower()
            if "11" in order_type or "take profit" in order_type or "tp" in order_type:
                tp_orders.append(order)
            elif "12" in order_type or "stop loss" in order_type or "sl" in order_type:
                sl_orders.append(order)
            
        # The test requires that TP and SL are correctly set in the system
        assert len(tp_orders) > 0, f"Take Profit order not found in system for {symbol}: {tpsl_data}"
        assert len(sl_orders) > 0, f"Stop Loss order not found in system for {symbol}: {tpsl_data}"
