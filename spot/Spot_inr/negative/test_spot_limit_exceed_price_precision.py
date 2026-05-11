"""
================================================================================
        SPOT LIMIT E2E TEST SUITE - NEGATIVE FLOW
================================================================================

Test Objective:
Validate that the Spot LIMIT order API correctly rejects orders when the
`price` field contains excessive decimal precision (e.g., >8 decimal places).

================================================================================
"""

import pytest
import allure
from config import Config
from clients.spot_client import SpotClient

pytestmark = pytest.mark.spot

@allure.feature("Spot E2E Flow - Negative")
@allure.story("Spot Limit Buy: Excessive Price Precision Validation")
@pytest.mark.spot
def test_spot_limit_exceed_price_precision():
    """
    Test Spot Limit Buy Negative Flow:
    Attempt to place a LIMIT order with excessive price precision and verify rejection.
    """
    spot_client = SpotClient()
    symbol = "BTC/INR"
    
    with allure.step("Step 1: Frame LIMIT order payload with excessive price precision"):
        # We prepare standard valid parameters, except price
        order_side = "BUY"
        quantity = "0.001"
        price = 123.1234567891

    with allure.step("Step 2: Send Spot LIMIT order request"):
        order_resp = spot_client.create_spot_limit_order(
            ctid=Config.DEFAULT_CTID,
            symbol=symbol,
            order_side=order_side,
            quantity=quantity,
            price=price
        )

    with allure.step("Step 3: Validate API rejection response"):
        assert isinstance(order_resp, dict), "Response must be a dictionary"
        
        # Verify the request correctly failed
        status = order_resp.get("Status", "")
        assert status in ["Failure", "Error"], f"Expected Failure/Error, got {status}. Response: {order_resp}"

    with allure.step("Step 4: Verify proper error message and status"):
        # Order should not be created, Data should not contain order_id
        data = order_resp.get("Data", {})
        if isinstance(data, dict):
            assert "order_id" not in data, "Order ID should not exist in the response!"
            assert "Id" not in data, "Order ID should not exist in the response!"

        # Verify that a meaningful error message is returned
        msg = order_resp.get("Message", order_resp.get("Msg", ""))
        assert msg != "", "Error message should not be empty"
        assert "price" in str(msg).lower() or "decimal" in str(msg).lower(), f"Error message should mention 'price' or 'decimal'. Got: {msg}"
        
        # Verify proper error code (usually 400 for bad request or local validation)
        code = order_resp.get("Code", -1)
        assert str(code) != "100", f"Expected failure code, got success code 100."
