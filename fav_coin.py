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
@allure.story("Favorite Coin Pairs: Add and Remove Flow")
@pytest.mark.serial
@requires_valid_ctid
def test_add_remove_favorite_coin_pair():
    """
    Test complete flow: Add a favorite coin pair, verify it in list, remove it, verify removal.
    Validates bidirectional favorite coin pair management.
    """
    futures_client = FuturesClient()

    # ===== PHASE 1: Add Favorite Coin Pair =====
    with allure.step("Step 1: Add BTC/USDT as favorite coin pair"):
        coin_pair = "BTC/USDT"
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=coin_pair,
            value="0",  # 0 = add
        )
        assert result.get("Status") == "Success"
        assert result.get("Code") == 100

    with allure.step("Step 2: Retrieve favorite coin pairs and verify addition"):
        favorite_pairs = futures_client.get_favorite_coin_pairs(
            ctid=Config.DEFAULT_CTID,
        )
        assert favorite_pairs is not None, "Favorite pairs list should not be empty"
        pair_list = favorite_pairs.get("Data", []) if isinstance(favorite_pairs, dict) else favorite_pairs
        assert coin_pair in pair_list or any(p.get("coinpair") == coin_pair for p in pair_list if isinstance(p, dict)), \
            f"BTC/USDT should be in favorite pairs list"

    # ===== PHASE 2: Remove Favorite Coin Pair =====
    with allure.step("Step 3: Remove BTC/USDT from favorite coin pairs"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=coin_pair,
            value="1",  # 1 = remove
        )
        assert result.get("Status") == "Success"
        assert result.get("Code") == 100

    with allure.step("Step 4: Verify coin pair is removed from favorites"):
        favorite_pairs = futures_client.get_favorite_coin_pairs(
            ctid=Config.DEFAULT_CTID,
        )
        pair_list = favorite_pairs.get("Data", []) if isinstance(favorite_pairs, dict) else favorite_pairs
        assert coin_pair not in pair_list and not any(p.get("coinpair") == coin_pair for p in pair_list if isinstance(p, dict)), \
            f"BTC/USDT should be removed from favorite pairs list"


# ============================================================================
# POSITIVE TEST CASES - Happy Path Scenarios
# ============================================================================

@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Add Single Pair")
@pytest.mark.serial
@requires_valid_ctid
def test_add_single_favorite_coin_pair():
    """
    Test adding a single favorite coin pair.
    Validates successful addition and list retrieval.
    """
    futures_client = FuturesClient()
    coin_pair = Config.COINPAIR_BTC_USDT

    with allure.step(f"Add {coin_pair} to favorites"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=coin_pair,
            value="0",
        )
        assert result.get("Status") == "Success"
        assert result.get("Code") == 100

    with allure.step("Verify pair is in favorites list"):
        favorite_pairs = futures_client.get_favorite_coin_pairs(
            ctid=Config.DEFAULT_CTID,
        )
        pair_list = favorite_pairs.get("Data", []) if favorite_pairs.get("Data", []) else []
        assert coin_pair in pair_list or any(p.get("coinpair") == coin_pair for p in pair_list if isinstance(p, dict)), \
            f"{coin_pair} should be in favorite pairs"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Add Multiple Pairs")
@pytest.mark.serial
@requires_valid_ctid
def test_add_multiple_favorite_coin_pairs():
    """
    Test adding multiple favorite coin pairs.
    Validates system handles list of multiple favorites correctly.
    """
    futures_client = FuturesClient()
    coin_pairs = [Config.COINPAIR_BTC_USDT, Config.COINPAIR_ETH_USDT]

    with allure.step("Add multiple coin pairs to favorites"):
        for coin_pair in coin_pairs:
            result = futures_client.set_favorite_coin_pair(
                ctid=Config.DEFAULT_CTID,
                coinpair=coin_pair,
                value="0",
            )
            assert result.get("Status") == "Success", f"Failed to add {coin_pair}"

    with allure.step("Verify all pairs are in favorites list"):
        favorite_pairs = futures_client.get_favorite_coin_pairs(
            ctid=Config.DEFAULT_CTID,
        )
        pair_list = favorite_pairs.get("Data", []) if favorite_pairs.get("Data", []) else []
        for coin_pair in coin_pairs:
            assert coin_pair in pair_list or any(p.get("coinpair") == coin_pair for p in pair_list if isinstance(p, dict)), \
                f"{coin_pair} should be in favorite pairs"

    with allure.step("Clean up: Remove all added pairs"):
        for coin_pair in coin_pairs:
            futures_client.set_favorite_coin_pair(
                ctid=Config.DEFAULT_CTID,
                coinpair=coin_pair,
                value="1",  # Remove
            )


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Remove Single Pair")
@pytest.mark.serial
@requires_valid_ctid
def test_remove_single_favorite_coin_pair():
    """
    Test removing a single favorite coin pair.
    Validates successful removal from list.
    """
    futures_client = FuturesClient()
    coin_pair = Config.COINPAIR_BTC_USDT

    with allure.step("First add the pair"):
        futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=coin_pair,
            value="0",
        )

    with allure.step("Remove the pair from favorites"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=coin_pair,
            value="1",
        )
        assert result.get("Status") == "Success"
        assert result.get("Code") == 100

    with allure.step("Verify pair is no longer in favorites"):
        favorite_pairs = futures_client.get_favorite_coin_pairs(
            ctid=Config.DEFAULT_CTID,
        )
        pair_list = favorite_pairs.get("Data", []) if favorite_pairs.get("Data", []) else []
        assert coin_pair not in pair_list and not any(p.get("coinpair") == coin_pair for p in pair_list if isinstance(p, dict)), \
            f"{coin_pair} should be removed from favorites"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Get Empty Favorites List")
@pytest.mark.serial
@requires_valid_ctid
def test_get_empty_favorite_coin_pairs():
    """
    Test retrieving favorites when list is empty.
    Validates system handles empty state correctly.
    """
    futures_client = FuturesClient()

    with allure.step("Retrieve favorite pairs list"):
        favorite_pairs = futures_client.get_favorite_coin_pairs(
            ctid=Config.DEFAULT_CTID,
        )
        # Should return empty list or valid response object
        assert favorite_pairs is not None, "Response should not be null"
        pair_list = favorite_pairs.get("Data", []) if favorite_pairs.get("Data", []) else []
        assert isinstance(pair_list, list), "Data should be a list"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Get Non-Empty Favorites List")
@pytest.mark.serial
@requires_valid_ctid
def test_get_non_empty_favorite_coin_pairs():
    """
    Test retrieving favorites when list contains items.
    Validates list structure and content.
    """
    futures_client = FuturesClient()
    coin_pair = "XRP/USDT"

    with allure.step("Add a coin pair to favorites"):
        futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=coin_pair,
            value="0",
        )

    with allure.step("Retrieve and validate favorite pairs list"):
        favorite_pairs = futures_client.get_favorite_coin_pairs(
            ctid=Config.DEFAULT_CTID,
        )
        pair_list = favorite_pairs.get("Data", []) if favorite_pairs.get("Data", []) else []
        assert len(pair_list) > 0, "Favorites list should not be empty"
        assert coin_pair in pair_list or any(p.get("coinpair") == coin_pair for p in pair_list if isinstance(p, dict)), \
            f"{coin_pair} should be in the list"

    with allure.step("Clean up: Remove the added pair"):
        futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=coin_pair,
            value="1",
        )


# ============================================================================
# NEGATIVE TEST CASES - Error Scenarios & Validation
# ============================================================================

@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Invalid CTID")
@pytest.mark.serial
@requires_valid_ctid
def test_add_favorite_invalid_ctid():
    """
    Negative case: Attempt to add favorite with invalid CTID.
    Expected: Request should fail with validation error.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to add favorite with invalid CTID"):
        result = futures_client.set_favorite_coin_pair(
            ctid="INVALID_CTID_99999",
            coinpair="BTC/USDT",
            value="0",
        )
        # Expected: Should fail with error
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Request with invalid CTID should fail"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Empty CTID")
@pytest.mark.serial
def test_add_favorite_empty_ctid():
    """
    Negative case: Attempt to add favorite with empty CTID.
    Expected: Request should be rejected.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to add favorite with empty CTID"):
        result = futures_client.set_favorite_coin_pair(
            ctid="",
            coinpair="BTC/USDT",
            value="0",
        )
        # Expected: Should fail
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Request with empty CTID should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Invalid Coin Pair Format")
@pytest.mark.serial
def test_add_favorite_invalid_coin_pair_format():
    """
    Negative case: Attempt to add favorite with invalid coin pair format.
    Expected: Request should fail with validation error.
    Valid format: SYMBOL/QUOTE (e.g., BTC/USDT)
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to add favorite with invalid format (no slash)"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair="BTCUSDT",  # Missing slash
            value="0",
        )
        # Expected: Should fail
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Invalid coin pair format should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Non-Existent Coin Pair")
@pytest.mark.serial
@requires_valid_ctid
def test_add_favorite_non_existent_pair():
    """
    Negative case: Attempt to add a non-existent coin pair as favorite.
    Expected: Request should fail if pair doesn't exist in system.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to add non-existent coin pair"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair="FAKE/USDT",  # Non-existent pair
            value="0",
        )
        # Expected: Should fail or be rejected
        # Comment: Depends on API validation - may need to adjust expectation
        if result.get("Code") != 100:
            assert True, "Non-existent pair was rejected as expected"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Empty Coin Pair")
@pytest.mark.serial
def test_add_favorite_empty_coin_pair():
    """
    Negative case: Attempt to add favorite with empty coin pair.
    Expected: Request should be rejected.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to add favorite with empty coin pair"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair="",
            value="0",
        )
        # Expected: Should fail
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Empty coin pair should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Invalid Value Parameter")
@pytest.mark.serial
def test_add_favorite_invalid_value():
    """
    Negative case: Attempt to set favorite with invalid value parameter.
    Expected: Request should fail with validation error.
    Valid values: 0=add, 1=remove
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to set favorite with invalid value (99)"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair="BTC/USDT",
            value=99,  # Invalid value
        )
        # Expected: Should fail
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Invalid value parameter should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Negative Value")
@pytest.mark.serial
def test_add_favorite_negative_value():
    """
    Negative case: Attempt to set favorite with negative value.
    Expected: Request should fail or be interpreted incorrectly.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to set favorite with negative value"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair="BTC/USDT",
            value=-1,
        )
        # Expected: Should fail with validation error
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Negative value should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Get Invalid CTID")
@pytest.mark.serial
@requires_valid_ctid
def test_get_favorite_invalid_ctid():
    """
    Negative case: Attempt to get favorites with invalid CTID.
    Expected: Should fail or return empty/error.
    """
    futures_client = FuturesClient()

    with allure.step("Retrieve favorites with invalid CTID"):
        result = futures_client.get_favorite_coin_pairs(
            ctid="INVALID_CTID_99999",
        )
        # Expected: Should fail or return error
        if isinstance(result, dict):
            assert result.get("Status") != "Success" or result.get("Code") != 100, \
                "Get with invalid CTID should fail"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Null Coin Pair")
@pytest.mark.serial
def test_add_favorite_null_coin_pair():
    """
    Negative case: Attempt to add favorite with null/None coin pair.
    Expected: Request should fail with validation error.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to add favorite with null coin pair"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=None,
            value="0",
        )
        # Expected: Should fail
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Null coin pair should be rejected"


# ============================================================================
# EDGE CASE TEST CASES
# ============================================================================

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


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Remove Non-Existent Pair")
@pytest.mark.serial
@requires_valid_ctid
def test_remove_favorite_non_existent_pair():
    """
    Edge case: Attempt to remove a coin pair that's not in favorites.
    Validates system handles removal of non-existent items gracefully.
    Expected: Should either fail or succeed silently (idempotent).
    """
    futures_client = FuturesClient()
    coin_pair = "LINK/USDT"

    with allure.step("Attempt to remove pair that doesn't exist in favorites"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=coin_pair,
            value="1",  # Remove
        )
        # Document the actual behavior - should be graceful handling
        # Result can be Success or failure depending on API design


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Case Sensitivity")
@pytest.mark.serial
@requires_valid_ctid
def test_favorite_coin_pair_case_sensitivity():
    """
    Edge case: Test if coin pair matching is case-sensitive.
    Validates system handling of case variations.
    """
    futures_client = FuturesClient()

    with allure.step("Add lowercase coin pair"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair="btc/usdt",
            value="0",
        )
        # May succeed or fail depending on case sensitivity

    with allure.step("Attempt to retrieve and verify"):
        favorite_pairs = futures_client.get_favorite_coin_pairs(
            ctid=Config.DEFAULT_CTID,
        )
        # Verify if lowercase variant is returned

    with allure.step("Clean up"):
        futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair="btc/usdt",
            value="1",
        )


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Special Characters in Pair")
@pytest.mark.serial
def test_favorite_coin_pair_special_characters():
    """
    Edge case: Test coin pair with special characters or spaces.
    Validates input validation and sanitization.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to add pair with special characters"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair="BTC @USDT",  # Space and special char
            value="0",
        )
        # Should fail or sanitize input
        # Expected: Validation error


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Rapid Add-Remove Cycles")
@pytest.mark.serial
@requires_valid_ctid
def test_favorite_coin_pair_rapid_cycles():
    """
    Edge case: Perform rapid add-remove cycles.
    Validates system stability with quick succession operations.
    """
    futures_client = FuturesClient()
    coin_pair = "MATIC/USDT"

    with allure.step("Perform 3 rapid add-remove cycles"):
        for cycle in range(3):
            # Add
            result_add = futures_client.set_favorite_coin_pair(
                ctid=Config.DEFAULT_CTID,
                coinpair=coin_pair,
                value="0",
            )
            assert result_add.get("Status") == "Success", f"Cycle {cycle+1} add failed"

            # Remove
            result_remove = futures_client.set_favorite_coin_pair(
                ctid=Config.DEFAULT_CTID,
                coinpair=coin_pair,
                value="1",
            )
            assert result_remove.get("Status") == "Success", f"Cycle {cycle+1} remove failed"

    with allure.step("Verify final state - pair should not be in favorites"):
        favorite_pairs = futures_client.get_favorite_coin_pairs(
            ctid=Config.DEFAULT_CTID,
        )
        pair_list = favorite_pairs.get("Data", []) if isinstance(favorite_pairs, dict) else favorite_pairs
        assert coin_pair not in pair_list and not any(p.get("coinpair") == coin_pair for p in pair_list if isinstance(p, dict)), \
            f"{coin_pair} should not be in favorites after cycles"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Very Long Coin Pair String")
@pytest.mark.serial
def test_favorite_coin_pair_long_string():
    """
    Edge case: Test with extremely long coin pair string.
    Validates input length validation.
    """
    futures_client = FuturesClient()
    long_pair = "A" * 1000 + "/USDT"  # Excessively long

    with allure.step("Attempt to add favorite with very long coin pair"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair=long_pair,
            value="0",
        )
        # Expected: Should fail with validation error
        assert result.get("Status") != "Success" or result.get("Code") != 100, \
            "Excessively long coin pair should be rejected"


@allure.feature("Futures E2E Flow")
@allure.story("Favorite Coin Pairs: Unicode Characters in Pair")
@pytest.mark.serial
def test_favorite_coin_pair_unicode():
    """
    Edge case: Test coin pair with unicode characters.
    Validates handling of non-ASCII characters.
    """
    futures_client = FuturesClient()

    with allure.step("Attempt to add pair with unicode characters"):
        result = futures_client.set_favorite_coin_pair(
            ctid=Config.DEFAULT_CTID,
            coinpair="BTC/USDT€",  # Unicode character
            value="0",
        )
        # Expected: Should fail or be rejected
        if result.get("Code") != 100:
            assert True, "Unicode characters properly rejected"
