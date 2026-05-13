"""
================================================================================
        SPOT LIMIT E2E TEST SUITE - NEGATIVE FLOW
================================================================================

Test Objective:
Validate that the Spot LIMIT order API correctly rejects orders when the
`quantity` field is an empty string ("").

================================================================================
"""

import pytest
import allure
from config import Config
from clients.spot_client import SpotClient

pytestmark = pytest.mark.spot

@allure.feature("Spot E2E Flow - Negative")
@allure.story("Spot Limit Buy: Empty Quantity Validation")
@pytest.mark.spot
def test_spot_limit_empty_quantity():
    """
    Test Spot Limit Buy Negative Flow:
    Attempt to place a LIMIT order with an empty quantity ("") and verify rejection.
    """
    spot_client = SpotClient()
    symbol = "BTC/USDT"
    
    with allure.step("Step 1: Frame LIMIT order payload with quantity = \"\""):
        # We prepare standard valid parameters, except quantity
        order_side = "BUY"
        quantity = ""
        price = "60000.0"

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
        assert "quantity" in str(msg).lower(), f"Error message should mention 'quantity'. Got: {msg}"
        
        # Verify proper error code (usually 400 for bad request or local validation)
        code = order_resp.get("Code", -1)
        assert str(code) != "100", f"Expected failure code, got success code 100."
