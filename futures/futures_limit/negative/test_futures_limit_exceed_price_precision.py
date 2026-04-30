"""
================================================================================
        FUTURES LIMIT E2E TEST SUITE - PRICE PRECISION OVERFLOW
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
│ NEGATIVE TEST                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ • test_futures_limit_exceed_price_precision()                                                   │
│   → Price precision overflow                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                            EXECUTION NOTES
================================================================================

• Test uses @pytest.mark.serial
• Safe for parallel execution

Example Execution:
  pytest futures_limit/negative/test_futures_limit_exceed_price_precision.py -v
  pytest futures_limit/negative/test_futures_limit_exceed_price_precision.py --alluredir=allure-results

================================================================================
"""

import pytest
import allure
from config import Config

pytestmark = pytest.mark.serial

@allure.feature("Futures Limit Negative Tests")
@allure.story("Price precision overflow")
@pytest.mark.serial
def test_futures_limit_exceed_price_precision(setup_data):
    client = setup_data["client"]
    with allure.step("Send order with price exceeding allowed decimal precision"):
        resp = client.create_order(
            ctid=Config.DEFAULT_CTID, symbol=setup_data["symbol"], 
            qty=setup_data["valid_qty"], price="0.123456789012", 
            amount=setup_data["valid_amount"], order_type="1", order_side="0", leverage="5"
        )
        assert resp.get("Status") == "Error" or str(resp.get("Code")) != "100", f"Order should have failed but got: {resp}"

# ==============================================================================
# QUANTITY NEGATIVE TESTS
# ==============================================================================
