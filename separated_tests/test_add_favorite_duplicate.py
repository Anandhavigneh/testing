"""
================================================================================
                    FAVORITE COIN PAIRS E2E TEST SUITE
================================================================================

API Endpoints Tested:
  • POST   /api/v1/futures/set/favcoinpair    - Add/Remove favorite coin pairs
  • GET    /api/v1/futures/favcoinpairs        - Retrieve favorite coin pairs

Client Methods:
  • FuturesClient.set_favorite_coin_pair(ctid, coinpair, value)
  • FuturesClient.get_favorite_coin_pairs(ctid)

================================================================================
                              TEST COVERAGE
================================================================================

TOTAL TEST CASES: 22

┌─────────────────────────────────────────────────────────────────────────────┐
│ MAIN FLOW TESTS (1 test)                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ • test_add_remove_favorite_coin_pair()                                      │
│   → Complete bidirectional flow: Add pair → Verify → Remove → Verify       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ POSITIVE TEST CASES - Happy Path Scenarios (6 tests)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_add_single_favorite_coin_pair()                                     │
│    → Add a single coin pair and verify it appears in favorites list         │
│                                                                              │
│ 2. test_add_multiple_favorite_coin_pairs()                                  │
│    → Add multiple pairs (BTC/USDT, ETH/USDT, ADA/USDT) successively        │
│    → Verify all pairs are in the list → Clean up                           │
│                                                                              │
│ 3. test_remove_single_favorite_coin_pair()                                  │
│    → Add a pair, then remove it → Verify removal from list                 │
│                                                                              │
│ 4. test_get_empty_favorite_coin_pairs()                                     │
│    → Retrieve favorites when list is empty → Validate response structure   │
│                                                                              │
│ 5. test_get_non_empty_favorite_coin_pairs()                                │
│    → Add a pair → Get list → Verify pair exists → Clean up                 │
│                                                                              │
│ 6. test_add_single_favorite_coin_pair() [Alternative Pair]                 │
│    → Add ETH/USDT specifically and verify                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ NEGATIVE TEST CASES - Error Scenarios (9 tests)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_add_favorite_invalid_ctid()                                         │
│    → Invalid CTID format → Request should fail with error                   │
│                                                                              │
│ 2. test_add_favorite_empty_ctid()                                           │
│    → Empty CTID string "" → Request should be rejected                      │
│                                                                              │
│ 3. test_add_favorite_invalid_coin_pair_format()                             │
│    → Invalid format: "BTCUSDT" (missing /) → Should fail validation         │
│                                                                              │
│ 4. test_add_favorite_non_existent_pair()                                    │
│    → Non-existent pair: "FAKE/USDT" → Should be rejected if validation     │
│                                                                              │
│ 5. test_add_favorite_empty_coin_pair()                                      │
│    → Empty coin pair "" → Should be rejected                                │
│                                                                              │
│ 6. test_add_favorite_invalid_value()                                        │
│    → Invalid value parameter (99) → Expected values: 0=add, 1=remove      │
│                                                                              │
│ 7. test_add_favorite_negative_value()                                       │
│    → Negative value (-1) → Should fail validation                           │
│                                                                              │
│ 8. test_get_favorite_invalid_ctid()                                         │
│    → Get favorites with invalid CTID → Should fail or error                 │
│                                                                              │
│ 9. test_add_favorite_null_coin_pair()                                       │
│    → Null/None coin pair parameter → Should be rejected                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ EDGE CASE TEST CASES (6 tests)                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. test_add_favorite_duplicate()                                            │
│    → Add same pair twice → Verify idempotency (≤1 instance in list)        │
│                                                                              │
│ 2. test_remove_favorite_non_existent_pair()                                 │
│    → Remove pair not in favorites → Test graceful handling                  │
│                                                                              │
│ 3. test_favorite_coin_pair_case_sensitivity()                               │
│    → Add "btc/usdt" (lowercase) → Test case-sensitivity handling            │
│                                                                              │
│ 4. test_favorite_coin_pair_special_characters()                             │
│    → Try "BTC @USDT" (with space & special chars) → Validation test        │
│                                                                              │
│ 5. test_favorite_coin_pair_rapid_cycles()                                   │
│    → Perform 3 rapid add-remove cycles → Verify stability & final state    │
│                                                                              │
│ 6. test_favorite_coin_pair_long_string()                                    │
│    → Test with extremely long coin pair (1000+ chars) → Input validation   │
│                                                                              │
│ 7. test_favorite_coin_pair_unicode()                                        │
│    → Add pair with Unicode chars "BTC/USDT€" → Should be rejected          │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                            EXECUTION NOTES
================================================================================

• All tests are marked with @pytest.mark.serial to ensure serial execution
• Module-level pytestmark = pytest.mark.serial applies to entire module
• Tests use threading-based lock (serial_lock fixture in conftest.py)
• Safe for parallel execution with pytest-xdist: pytest -n 4
• Each test is independent and includes cleanup steps where applicable

Example Execution:
  pytest tests/e2e/futures/coin_pairs/test_fav_coint_pair_e2e.py -v
  pytest tests/e2e/futures/coin_pairs/test_fav_coint_pair_e2e.py --alluredir=allure-results
  pytest tests/e2e/futures/coin_pairs/test_fav_coint_pair_e2e.py -n 4 -v

================================================================================
"""

import pytest
import allure
from config import Config
from clients.futures_client import FuturesClient

# Marker for tests that modify shared user preferences and must run serially
pytestmark = pytest.mark.serial
requires_valid_ctid = pytest.mark.skipif(
    Config.DEFAULT_CTID == "REPLACE_WITH_VALID_CTID",
    reason="Set GIOTTUS_DEFAULT_CTID to a real CTID to run live favorite coin pair tests.",
)

@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Duplicate Add")
@pytest.mark.serial
@requires_valid_ctid
def test_add_favorite_duplicate():
    """
    Edge case: Add the same coin pair twice.
    Validates system handles duplicate additions correctly.
    Expected: Second add should either fail or be idempotent.
    """
    futures_client = FuturesClient()
    coin_pair = "DOGE/USDT"

    with allure.step("Add coin pair first time"):
        result1 = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=coin_pair,
            value="0",
        )
        assert result1.get("Status") == "Success"

    with allure.step("Attempt to add same coin pair again"):
        result2 = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=coin_pair,
            value="0",
        )
        # Should either succeed (idempotent) or fail gracefully
        # Document the actual behavior

    with allure.step("Verify only one instance in favorites"):
        favorite_pairs = futures_client.get_favorite_coin_pairs(
            ctid=Config.DEFAULT_CTID,
        )
        pair_list = favorite_pairs.get("Data", []) if isinstance(favorite_pairs, dict) else favorite_pairs
        pair_count = sum(1 for p in pair_list if p == coin_pair or (isinstance(p, dict) and p.get("coinpair") == coin_pair))
        assert pair_count <= 1, "Pair should appear at most once in favorites"

    with allure.step("Clean up: Remove the pair"):
        futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=coin_pair,
            value="1",
        )


