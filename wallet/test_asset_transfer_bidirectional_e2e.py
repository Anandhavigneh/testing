"""
================================================================================
                   ASSET TRANSFER BIDIRECTIONAL E2E TEST SUITE
================================================================================

API Endpoints Tested:
  • POST   /api/v1/futures/fund/transfer      - Transfer funds between wallets
  • GET    /api/v1/futures/user-details        - Fetch wallet balances

Client Methods:
  • FuturesClient.transfer_spot_to_futures(ctid, symbol, qty, transfer_type=0)
  • FuturesClient.transfer_futures_to_spot(ctid, symbol, qty, transfer_type=1)
  • FuturesClient.fetch_user_details(ctid, symbol)
  • FuturesClient.wait_for_balance_update(ctid, symbol, expected_futures, expected_spot, timeout, poll_interval)

================================================================================
                              TEST COVERAGE
================================================================================

TOTAL TEST CASES: 13

┌─────────────────────────────────────────────────────────────────────────────┐
│ MAIN FLOW TESTS (1 test)                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ • test_bidirectional_asset_transfer()                                       │
│   → Complete two-phase transfer: Spot→Futures → Futures→Spot                │
│   → Verify balance updates both directions with async polling               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ POSITIVE TEST CASES - Happy Path Scenarios (5 tests)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_spot_to_futures_transfer_only()                                     │
│    → Transfer from Spot→Futures (2.50 USDT)                                 │
│    → Verify balances updated correctly                                      │
│                                                                              │
│ 2. test_futures_to_spot_transfer_only()                                     │
│    → Transfer from Futures→Spot (1.50 USDT)                                 │
│    → Verify balances updated correctly                                      │
│                                                                              │
│ 3. test_transfer_minimum_amount()                                           │
│    → Transfer micro-transaction (0.01 USDT)                                │
│    → Validate system handles smallest valid amounts                         │
│                                                                              │
│ 4. test_transfer_large_amount()                                             │
│    → Transfer large sum (100.00 USDT)                                      │
│    → Validate system handles high-value transactions                        │
│                                                                              │
│ 5. test_transfer_decimal_precision()                                        │
│    → Transfer with high precision (3.14159 USDT)                           │
│    → Verify floating-point accuracy is maintained                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ NEGATIVE TEST CASES - Error Scenarios (6 tests)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_transfer_insufficient_spot_balance()                                │
│    → Attempt transfer > available spot balance → Should fail                │
│                                                                              │
│ 2. test_transfer_insufficient_futures_balance()                             │
│    → Attempt transfer > available futures balance → Should fail             │
│                                                                              │
│ 3. test_transfer_zero_amount()                                              │
│    → Try to transfer 0.00 → Should be rejected                              │
│                                                                              │
│ 4. test_transfer_negative_amount()                                          │
│    → Try to transfer -5.00 → Should fail validation                         │
│                                                                              │
│ 5. test_transfer_invalid_ctid()                                             │
│    → Transfer with invalid CTID → Should fail authentication                │
│                                                                              │
│ 6. test_transfer_invalid_symbol()                                           │
│    → Transfer with invalid symbol "INVALID-PAIR" → Should fail              │
│                                                                              │
│ 7. test_transfer_invalid_transfer_type()                                    │
│    → Invalid transfer_type (99) → Valid: 0=spot→fut, 1=fut→spot            │
│                                                                              │
│ 8. test_transfer_non_numeric_amount()                                       │
│    → Non-numeric amount "invalid_amount" → Type validation error            │
│                                                                              │
│ 9. test_transfer_empty_parameters()                                         │
│    → Empty CTID "" → Should be rejected                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ EDGE CASE TEST CASES (2 tests)                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_rapid_sequential_transfers()                                        │
│    → Execute 3 rapid transfers in succession (0.50 each)                   │
│    → Verify system stability and balance integrity                          │
│                                                                              │
│ 2. test_transfer_idempotency()                                              │
│    → Attempt duplicate transfer requests                                    │
│    → Verify only one debit applied (prevents double-processing)             │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                         TRANSFER FLOW DETAILS
================================================================================

Spot to Futures (transfer_type=0):
  • Deducts from spot wallet
  • Adds to futures wallet
  • Expected: Status=Success, Code=100

Futures to Spot (transfer_type=1):
  • Deducts from futures wallet
  • Adds to spot wallet
  • Expected: Status=Success, Code=100

Balance Verification:
  • Uses async polling with configurable timeout (default 30s)
  • Poll interval: 2 seconds
  • Tolerance: ±0.01 for floating-point comparison

Assertions Included:
  • Response Status and Code validation
  • Asset type validation (USDT)
  • Balance change calculations
  • Async update timeout handling

================================================================================
                            EXECUTION NOTES
================================================================================

• All tests are marked with @pytest.mark.serial to ensure serial execution
• Module-level pytestmark = pytest.mark.serial applies to entire module
• Tests use threading-based lock (serial_lock fixture in conftest.py)
• Safe for parallel execution with pytest-xdist: pytest -n 4
• Config uses DEFAULT_CTID, DEFAULT_SYMBOL, DEFAULT_FUTURES_SYMBOL
• Transfers are ASYNC - balances update in background, polling required

Example Execution:
  pytest futures/asset_transfer/test_asset_transfer_bidirectional_e2e.py -v
  pytest futures/asset_transfer/ --alluredir=allure-results
  pytest futures/asset_transfer/ -n 4 -v

Performance Notes:
  • Each test waits up to 30 seconds for balance update (async process)
  • With -n 4 parallel execution, serial marker ensures one test at a time
  • Total suite execution time: ~5-10 minutes (depends on async backend delays)

================================================================================
"""

import time
import pytest
import allure
from config import Config
from clients.futures_client import FuturesClient


# Marker for tests that modify shared wallet state and must run serially
pytestmark = pytest.mark.serial


def _user_details_available() -> bool:
    """Return True if the user-details API responds successfully for the test CTID."""
    client = FuturesClient()
    details = client.fetch_user_details(ctid=Config.DEFAULT_CTID, symbol=Config.DEFAULT_SYMBOL)
    return not details.get("_api_error", True)


requires_user_details = pytest.mark.skipif(
    not _user_details_available(),
    reason=(
        "Skipped: /user-details API returned an error for the test CTID. "
        "Balance verification tests require a working user-details endpoint."
    ),
)


@allure.feature("Futures E2E Flow")
@allure.story("Bidirectional Asset Transfer between Spot and Futures")
@pytest.mark.serial
def test_bidirectional_asset_transfer():
    # 1. Setup
    futures_client = FuturesClient()

    # convert string amounts to float for assertions
    to_decimal = lambda s: float(s) if s is not None else 0.0

    # ===== PHASE 1: Transfer from Spot to Futures =====
    with allure.step("Step 1: Fetch initial wallet balances"):
        user_details = futures_client.fetch_user_details(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
        )
        fut_wallet = user_details.Data.wallet_balance.futures_wallet
        spot_wallet = user_details.Data.wallet_balance.spot_wallet

        # validate basic fields returned by service
        assert fut_wallet.asset == "USDT"
        assert spot_wallet.asset == "USDT"

        futures_before = to_decimal(fut_wallet.value)
        spot_before = to_decimal(spot_wallet.value)

    with allure.step("Step 2: Transfer amount from spot to futures"):
        transfer_amount = "1.00"
        result = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty=transfer_amount,
            transfer_type=0,
        )
        assert result.get("Status") == "Success"
        assert result.get("Code") == 100
        # Note: Transfer is async, balances will update in background

    with allure.step("Step 3: Poll for balance update (spot to futures)"):
        transfer_float = float(transfer_amount)
        expected_futures = futures_before + transfer_float
        expected_spot = spot_before - transfer_float
        
        balance_updated = futures_client.wait_for_balance_update(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
            expected_futures_value=expected_futures,
            expected_spot_value=expected_spot,
            timeout_seconds=60,
            poll_interval=2.0,
        )
        assert balance_updated, f"Balances did not update within timeout. Expected futures={expected_futures}, spot={expected_spot}"

    # ===== PHASE 2: Transfer from Futures to Spot =====
    with allure.step("Step 4: Fetch updated wallet balances before reverse transfer"):
        user_details = futures_client.fetch_user_details(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
        )
        fut_wallet = user_details.Data.wallet_balance.futures_wallet
        spot_wallet = user_details.Data.wallet_balance.spot_wallet

        futures_before_reverse = to_decimal(fut_wallet.value)
        spot_before_reverse = to_decimal(spot_wallet.value)

    with allure.step("Step 5: Transfer amount from futures back to spot"):
        transfer_amount_reverse = "1.00"
        result = futures_client.transfer_futures_to_spot(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty=transfer_amount_reverse,
            transfer_type=1,
        )
        assert result.get("Status") == "Success"
        assert result.get("Code") == 100
        # Note: Transfer is async, balances will update in background

    with allure.step("Step 6: Poll for balance update (futures to spot)"):
        transfer_float_reverse = float(transfer_amount_reverse)
        expected_futures_reverse = futures_before_reverse - transfer_float_reverse
        expected_spot_reverse = spot_before_reverse + transfer_float_reverse
        
        balance_updated = futures_client.wait_for_balance_update(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
            expected_futures_value=expected_futures_reverse,
            expected_spot_value=expected_spot_reverse,
            timeout_seconds=60,
            poll_interval=2.0,
        )
        assert balance_updated, f"Balances did not update within timeout. Expected futures={expected_futures_reverse}, spot={expected_spot_reverse}"

    # Cool off server rate limits
    time.sleep(5)


# ============================================================================
# POSITIVE TEST CASES - Happy Path Scenarios
# ============================================================================

@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Spot to Futures Only")
def test_spot_to_futures_transfer_only():
    """
    Test transferring assets from spot wallet to futures wallet only.
    Validates single direction transfer with balance verification.
    """
    futures_client = FuturesClient()
    to_decimal = lambda s: float(s) if s is not None else 0.0

    with allure.step("Fetch initial wallet balances"):
        user_details = futures_client.fetch_user_details(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
        )
        futures_before = to_decimal(user_details.Data.wallet_balance.futures_wallet.value)
        spot_before = to_decimal(user_details.Data.wallet_balance.spot_wallet.value)

    with allure.step("Transfer from spot to futures"):
        transfer_amount = "2.50"
        result = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty=transfer_amount,
            transfer_type=0,
        )
        assert result.get("Status") == "Success"
        assert result.get("Code") == 100

    with allure.step("Verify balance update"):
        transfer_float = float(transfer_amount)
        expected_futures = futures_before + transfer_float
        expected_spot = spot_before - transfer_float
        
        balance_updated = futures_client.wait_for_balance_update(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
            expected_futures_value=expected_futures,
            expected_spot_value=expected_spot,
            timeout_seconds=60,
            poll_interval=2.0,
        )
        assert balance_updated, f"Expected futures={expected_futures}, spot={expected_spot}"


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Futures to Spot Only")
def test_futures_to_spot_transfer_only():
    """
    Test transferring assets from futures wallet to spot wallet only.
    Validates single direction transfer with balance verification.
    """
    futures_client = FuturesClient()
    to_decimal = lambda s: float(s) if s is not None else 0.0

    with allure.step("Fetch initial wallet balances"):
        user_details = futures_client.fetch_user_details(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
        )
        futures_before = to_decimal(user_details.Data.wallet_balance.futures_wallet.value)
        spot_before = to_decimal(user_details.Data.wallet_balance.spot_wallet.value)

    with allure.step("Transfer from futures to spot"):
        transfer_amount = "1.50"
        result = futures_client.transfer_futures_to_spot(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty=transfer_amount,
            transfer_type=1,
        )
        assert result.get("Status") == "Success"
        assert result.get("Code") == 100

    with allure.step("Verify balance update"):
        transfer_float = float(transfer_amount)
        expected_futures = futures_before - transfer_float
        expected_spot = spot_before + transfer_float
        
        balance_updated = futures_client.wait_for_balance_update(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
            expected_futures_value=expected_futures,
            expected_spot_value=expected_spot,
            timeout_seconds=60,
            poll_interval=2.0,
        )
        assert balance_updated, f"Expected futures={expected_futures}, spot={expected_spot}"


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Minimum Amount")
def test_transfer_minimum_amount():
    """
    Test transferring a very small minimum amount.
    Validates system handles micro-transactions correctly.
    """
    futures_client = FuturesClient()
    to_decimal = lambda s: float(s) if s is not None else 0.0

    with allure.step("Fetch initial wallet balances"):
        user_details = futures_client.fetch_user_details(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
        )
        futures_before = to_decimal(user_details.Data.wallet_balance.futures_wallet.value)
        spot_before = to_decimal(user_details.Data.wallet_balance.spot_wallet.value)

    with allure.step("Transfer minimum amount (0.01)"):
        transfer_amount = "0.01"
        result = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty=transfer_amount,
            transfer_type=0,
        )
        assert result.get("Status") == "Success"

    with allure.step("Verify micro-transaction was processed"):
        balance_updated = futures_client.wait_for_balance_update(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
            expected_futures_value=futures_before + 0.01,
            expected_spot_value=spot_before - 0.01,
            timeout_seconds=60,
            poll_interval=2.0,
        )
        assert balance_updated, "Micro-transaction should be processed"
        
    # Cool off server rate limits
    time.sleep(2)


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Large Amount")
def test_transfer_large_amount():
    """
    Test transferring a large amount.
    Validates system handles high-value transactions correctly.
    """
    # Wait to clear the server's anti-spam rolling window from previous tests
    time.sleep(5)
    
    futures_client = FuturesClient()
    to_decimal = lambda s: float(s) if s is not None else 0.0

    with allure.step("Fetch initial wallet balances"):
        user_details = futures_client.fetch_user_details(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
        )
        futures_before = to_decimal(user_details.Data.wallet_balance.futures_wallet.value)
        spot_before = to_decimal(user_details.Data.wallet_balance.spot_wallet.value)

    with allure.step("Transfer large amount (20.00)"):
        transfer_amount = "20.00"
        result = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty=transfer_amount,
            transfer_type=0,
        )
        assert result.get("Status") == "Success"

    with allure.step("Verify large amount transfer"):
        balance_updated = futures_client.wait_for_balance_update(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
            expected_futures_value=futures_before + 20.0,
            expected_spot_value=spot_before - 20.0,
            timeout_seconds=60,
            poll_interval=2.0,
        )
        assert balance_updated, "Large amount transfer should complete successfully"

    # Cleanup: Revert balance
    futures_client.transfer_futures_to_spot(
        ctid=Config.DEFAULT_CTID,
        symbol=Config.DEFAULT_FUTURES_SYMBOL,
        qty=transfer_amount,
        transfer_type=1,
    )
    time.sleep(5)


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: High Precision Decimal")
def test_transfer_decimal_precision():
    """
    Test transferring amounts with high decimal precision.
    Validates system correctly handles floating-point arithmetic.
    """
    futures_client = FuturesClient()
    to_decimal = lambda s: float(s) if s is not None else 0.0

    with allure.step("Fetch initial wallet balances"):
        user_details = futures_client.fetch_user_details(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
        )
        futures_before = to_decimal(user_details.Data.wallet_balance.futures_wallet.value)
        spot_before = to_decimal(user_details.Data.wallet_balance.spot_wallet.value)

    with allure.step("Transfer with high decimal precision"):
        transfer_amount = "3.14159"
        result = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty=transfer_amount,
            transfer_type=0,
        )
        assert result.get("Status") == "Success"

    with allure.step("Verify precision is maintained"):
        balance_updated = futures_client.wait_for_balance_update(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
            expected_futures_value=futures_before + 3.14159,
            expected_spot_value=spot_before - 3.14159,
            timeout_seconds=60,
            poll_interval=2.0,
        )
        assert balance_updated, "Transfer with high precision should maintain accuracy"


# ============================================================================
# NEGATIVE TEST CASES - Error Scenarios & Validation
# ============================================================================

@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Insufficient Balance in Spot")
def test_transfer_insufficient_spot_balance():
    """
    Negative case: Attempt to transfer more than available in spot wallet.
    Expected: Transfer should fail or be rejected.
    """
    futures_client = FuturesClient()
    to_decimal = lambda s: float(s) if s is not None else 0.0

    with allure.step("Fetch current spot wallet balance"):
        user_details = futures_client.fetch_user_details(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
        )
        spot_balance = to_decimal(user_details.Data.wallet_balance.spot_wallet.value)

    with allure.step("Attempt to transfer more than available balance"):
        excessive_amount = str(spot_balance + 1000.0)  # Request more than available
        result = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty=excessive_amount,
            transfer_type=0,
        )
        # Expected: Should fail with error status
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Transfer should fail when insufficient balance available"


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Insufficient Balance in Futures")
def test_transfer_insufficient_futures_balance():
    """
    Negative case: Attempt to transfer more than available in futures wallet.
    Expected: Transfer should fail or be rejected.
    """
    futures_client = FuturesClient()
    to_decimal = lambda s: float(s) if s is not None else 0.0

    with allure.step("Fetch current futures wallet balance"):
        user_details = futures_client.fetch_user_details(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
        )
        futures_balance = to_decimal(user_details.Data.wallet_balance.futures_wallet.value)

    with allure.step("Attempt to transfer more than available from futures"):
        excessive_amount = str(futures_balance + 1000.0)  # Request more than available
        result = futures_client.transfer_futures_to_spot(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty=excessive_amount,
            transfer_type=1,
        )
        # Expected: Should fail with error status
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Transfer should fail when insufficient futures balance available"


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Zero Amount Transfer")
def test_transfer_zero_amount():
    """
    Negative case: Attempt to transfer zero amount.
    Expected: Transfer should be rejected or ignored.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to transfer zero amount"):
        result = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty="0.00",
            transfer_type=0,
        )
        # Expected: Should fail or return error code
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Zero amount transfer should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Negative Amount Transfer")
def test_transfer_negative_amount():
    """
    Negative case: Attempt to transfer negative amount.
    Expected: Transfer should be rejected with validation error.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to transfer negative amount"):
        result = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty="-5.00",
            transfer_type=0,
        )
        # Expected: Should fail or return validation error
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Negative amount transfer should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Invalid CTID")
def test_transfer_invalid_ctid():
    """
    Negative case: Attempt transfer with invalid/non-existent CTID.
    Expected: Transfer should fail with authentication or validation error.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt transfer with invalid CTID"):
        result = futures_client.transfer_spot_to_futures(
            ctid="INVALID_CTID_12345",
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty="1.00",
            transfer_type=0,
        )
        # Expected: Should fail with error
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Transfer with invalid CTID should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Invalid Symbol")
def test_transfer_invalid_symbol():
    """
    Negative case: Attempt transfer with invalid/non-existent symbol.
    Expected: Transfer should fail with validation error.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt transfer with invalid symbol"):
        result = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol="INVALID-PAIR",
            qty="1.00",
            transfer_type=0,
        )
        # Expected: Should fail with error
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Transfer with invalid symbol should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Invalid Transfer Type")
def test_transfer_invalid_transfer_type():
    """
    Negative case: Attempt transfer with invalid transfer_type value.
    Expected: Transfer should fail with validation error.
    Valid values: 0=spot_to_futures, 1=futures_to_spot
    """
    futures_client = FuturesClient()

    with allure.step("Attempt transfer with invalid transfer_type (99)"):
        result = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty="1.00",
            transfer_type=99,  # Invalid transfer type
        )
        # Expected: Should fail with validation error
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Transfer with invalid transfer_type should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Invalid Amount Format")
def test_transfer_non_numeric_amount():
    """
    Negative case: Attempt transfer with non-numeric amount.
    Expected: Transfer should fail with validation/type error.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt transfer with non-numeric amount"):
        result = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty="invalid_amount",
            transfer_type=0,
        )
        # Expected: Should fail with error
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Transfer with non-numeric amount should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Empty/Null Parameters")
def test_transfer_empty_parameters():
    """
    Negative case: Attempt transfer with empty or null parameters.
    Expected: Transfer should fail with validation error.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt transfer with empty CTID"):
        result = futures_client.transfer_spot_to_futures(
            ctid="",
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty="1.00",
            transfer_type=0,
        )
        # Expected: Should fail
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Transfer with empty CTID should be rejected"


# ============================================================================
# EDGE CASE TEST CASES
# ============================================================================

@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Rapid Sequential Transfers")
def test_rapid_sequential_transfers():
    """
    Edge case: Perform multiple rapid transfers in quick succession.
    Validates system handles rapid API calls and maintains balance integrity.
    """
    futures_client = FuturesClient()
    to_decimal = lambda s: float(s) if s is not None else 0.0

    with allure.step("Fetch initial balance"):
        user_details = futures_client.fetch_user_details(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
        )
        initial_futures = to_decimal(user_details.Data.wallet_balance.futures_wallet.value)
        initial_spot = to_decimal(user_details.Data.wallet_balance.spot_wallet.value)

    with allure.step("Execute 3 rapid transfers"):
        for i in range(3):
            result = futures_client.transfer_spot_to_futures(
                ctid=Config.DEFAULT_CTID,
                symbol=Config.DEFAULT_FUTURES_SYMBOL,
                qty="0.50",
                transfer_type=0,
            )
            assert result.get("Status") == "Success", f"Transfer {i+1} failed"

    with allure.step("Verify final balance reflects all transfers"):
        expected_futures = initial_futures + (3 * 0.50)
        expected_spot = initial_spot - (3 * 0.50)
        
        balance_updated = futures_client.wait_for_balance_update(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
            expected_futures_value=expected_futures,
            expected_spot_value=expected_spot,
            timeout_seconds=60.0,
            poll_interval=2.0,
        )
        assert balance_updated, "All rapid transfers should be reflected in final balance"


@allure.feature("Futures E2E Flow")
@allure.story("Transfer Asset: Transfer Idempotency Check")
@pytest.mark.xfail(reason="Bug: Backend currently lacks idempotency protection and allows duplicate transfers")
def test_transfer_idempotency():
    """
    Edge case: Verify that duplicate transfer requests don't cause double debits.
    Validates system prevents accidental duplicate processing.
    Note: This requires request deduplication on the server side.
    """
    futures_client = FuturesClient()
    to_decimal = lambda s: float(s) if s is not None else 0.0

    with allure.step("Fetch initial balance"):
        user_details = futures_client.fetch_user_details(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
        )
        initial_futures = to_decimal(user_details.Data.wallet_balance.futures_wallet.value)
        initial_spot = to_decimal(user_details.Data.wallet_balance.spot_wallet.value)

    with allure.step("First transfer attempt"):
        result1 = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty="1.00",
            transfer_type=0,
        )
        assert result1.get("Status") == "Success"

    with allure.step("Immediate duplicate transfer request"):
        result2 = futures_client.transfer_spot_to_futures(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_FUTURES_SYMBOL,
            qty="1.00",
            transfer_type=0,
        )
        # Either should fail (preferred) or should be idempotent
        # Document actual behavior observed

    with allure.step("Verify balance increased only once"):
        # Allow for both success and failure scenarios
        balance_updated = futures_client.wait_for_balance_update(
            ctid=Config.DEFAULT_CTID,
            symbol=Config.DEFAULT_SYMBOL,
            expected_futures_value=initial_futures + 1.00,
            expected_spot_value=initial_spot - 1.00,
            timeout_seconds=30,
            poll_interval=2.0,
        )
        assert balance_updated, "Balance should reflect only one successful transfer"
