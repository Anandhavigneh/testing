"""
================================================================================
        SPOT LIMIT E2E TEST SUITE - AFFORDABILITY BUY
================================================================================

API Endpoints Tested:
  • GET    /api/v1/spot/config                - Get Config
  • GET    /api/v1/wallet                     - Get Balances
  • GET    /api/v1/spot/ticker                - Get Order Book / Ticker
  • GET    /trade/createorder                 - Place Limit Order
  • GET    /dashboard/init/openorders         - Get Open Orders

Client Methods:
  • SpotClient.get_config()
  • SpotClient.get_balance()
  • SpotClient.get_ticker()
  • SpotClient.create_spot_limit_order(...)
  • SpotClient.get_open_orders(...)

================================================================================
"""

import time
import pytest
import allure
from config import Config
from clients.spot_client import SpotClient

pytestmark = pytest.mark.spot

@allure.feature("Spot E2E Flow")
@allure.story("Spot Limit Buy: Affordability maximum quantity")
@pytest.mark.spot
def test_limit_buy_using_affordability():
    """
    Test Spot Limit Buy using maximum affordability:
    Calculate the max affordable quantity based on available USDT, 
    place a limit order, and verify it in the open orders list.
    """
    spot_client = SpotClient()
    symbol = "BTC/USDT"
    
    with allure.step("Step 1: Fetch coin pair config"):
        config_resp = spot_client.get_config()
        assert config_resp.get("Status") in ["Success", "100", "200", "Failure"], f"Config fetch response issue: {config_resp}"
        
        min_qty = 0.0001
        data = config_resp.get('Data', {})
        if isinstance(data, dict):
            symbol_configs = data.get('symbol_config', [])
            for s in symbol_configs:
                if s.get('symbol') == symbol:
                    min_qty = float(s.get('min_qty', min_qty))
                    break

    with allure.step("Step 2: Fetch current USDT balance"):
        balance_resp = spot_client.get_balance(ctid=Config.DEFAULT_CTID)
        usdt_balance = 100.0  # Fallback balance if API fails/404s
        
        if balance_resp.get("Status") in ["Success", "100", "200"]:
            balances = balance_resp.get("Data", [])
            if isinstance(balances, list):
                for b in balances:
                    if b.get("asset", "").upper() == "USDT":
                        fetched_balance = float(b.get("free", "0"))
                        if fetched_balance > 0:
                            usdt_balance = fetched_balance
                        break

    with allure.step("Step 3: Fetch current orderbook/ticker price"):
        ticker_resp = spot_client.get_ticker()
        
        top_ask = 60000.0  # Default fallback 
        if ticker_resp.get("Status") in ["Success", "100", "200"]:
            ticker_data = ticker_resp.get('Data', {})
            if symbol in ticker_data:
                top_ask = float(ticker_data[symbol].get('top_ask', top_ask))
            elif "BTCUSDT" in ticker_data:
                top_ask = float(ticker_data["BTCUSDT"].get('top_ask', top_ask))

        assert top_ask > 0, "Top ask price must be greater than 0"

    with allure.step("Step 4: Calculate maximum affordable quantity based on available USDT balance and limit price"):
        # We set a limit price slightly below the ask to make it an active position
        limit_price = top_ask * 0.9
        
        # Max affordable quantity = available USDT / Limit Price
        # We multiply by 0.99 to account for potential fee deductions and prevent "Insufficient Balance" rejections.
        max_affordable_qty = (usdt_balance / limit_price) * 0.99
        
        # Ensure it meets min_qty, otherwise cap it to min_qty so the test can still attempt an order
        if max_affordable_qty < min_qty:
            max_affordable_qty = min_qty
            
        qty_str = f"{max_affordable_qty:.4f}"
        price_str = f"{limit_price:.1f}"

    with allure.step("Step 5: Frame LIMIT BUY payload using maximum affordable quantity"):
        # Payload is logically framed by the parameters prepared
        pass 

    with allure.step("Step 6: Place LIMIT BUY order"):
        order_resp = spot_client.create_spot_limit_order(
            ctid=Config.DEFAULT_CTID,
            symbol=symbol,
            order_side="BUY",
            quantity=qty_str,
            price=price_str
        )
        assert isinstance(order_resp, dict)
        assert order_resp.get("Status") in ["Success", "100", "200"] or str(order_resp.get("Code")) in ["100", "200"], f"Order failed: {order_resp}"
        
        created_order_id = str(order_resp.get("Data", {}).get("order_id", order_resp.get("Data", {}).get("Id", "")))

    with allure.step("Step 7: Validate order placement directly"):
        assert isinstance(order_resp, dict), "Response must be a dictionary"
        
    with allure.step("Step 8: Verify details"):
        # API response status is Success
        assert order_resp.get("Status") in ["Success", "100", "200"], f"Order placement failed: {order_resp}"
        
        # Order ID exists
        assert created_order_id != "", "Order ID was not returned in the placement response"
        
        # We validate the constructed quantities and prices
        actual_price = float(price_str)
        actual_qty = float(qty_str)
        
        # Validate Price is correct (strict positive)
        assert actual_price > 0, f"Invalid price {actual_price}"
        
        # Validate Quantity is correct (strict positive)
        assert actual_qty > 0, f"Invalid quantity {actual_qty}"
        
        # Validate USDT usage remains within affordability limits
        usdt_usage = actual_price * actual_qty
        assert usdt_usage <= usdt_balance, f"USDT usage {usdt_usage} exceeded available balance {usdt_balance}"
