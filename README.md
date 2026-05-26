# Giottus E2E & API Testing Framework

This repository contains the comprehensive End-to-End (E2E) and API test suite for the Giottus trading platform. The framework is designed to validate spot trading, futures trading, bidirectional wallet transfers, and user preferences (favorite coins) against a testing environment.

The testing framework is built using **pytest** for test execution and suite management, and integrated with **Allure** for rich visual reporting and test run analytics.

---

## 1. Project Overview

The testing suite automates E2E user scenarios and API validations. Key components include:
*   **API Verification:** Direct validation of HTTP endpoints, response codes, data integrity, error payloads, and edge cases.
*   **Spot Trading E2E:** Order creation, cancellation, and validation for both USDT and INR markets.
*   **Futures Trading E2E:** Position management, leverage configurations, limit/market orders, Take-Profit/Stop-Loss (TP/SL) attachments, and reduce-only orders.
*   **Wallet Transfers:** Verification of bidirectional asset transfer flows.
*   **Favorite Coins:** Custom configuration and preference listing validations.

---

## 2. Project Structure

The project directory is structured as follows:

```text
testing/
├── clients/                       # HTTP API Clients wrapping the exchange endpoints
│   ├── spot_client.py             # Client for Spot market configurations & wallets
│   ├── futures_client.py          # Client for Futures market config & user details
│   └── futures_trading_client.py  # Client for placing orders, TPSL, positions, etc.
├── futures/                       # Futures E2E & limit/market trading test suite
│   ├── conftest.py                # Shared fixtures for Futures test runs
│   ├── test_futures_limit_e2e.py  # Comprehensive E2E Futures Limit trading scenarios
│   ├── test_futures_market_e2e.py # E2E Futures Market trading scenarios
│   ├── test_futures_position_e2e.py # Futures Position E2E validations
│   └── futures_limit/             # Sub-suites targeting detailed futures limit trading
│       ├── positive/              # Positive scenarios (leverage, reduce-only, tpsl, long/short)
│       └── negative/              # Negative edge cases and validation checks
├── spot/                          # Spot E2E trading test suite
│   ├── conftest.py                # Shared fixtures for Spot test runs
│   ├── test_spot_limit_e2e.py     # E2E Spot Limit trading scenarios
│   ├── test_spot_market_e2e.py    # E2E Spot Market trading scenarios
│   ├── spot_usdt/                 # USDT-specific spot tests (positive & negative)
│   └── Spot_inr/                  # INR-specific spot tests (positive & negative)
├── wallet/                        # Wallet E2E transfer tests
│   ├── conftest.py                # Shared fixtures for wallet transfers
│   └── test_asset_transfer_bidirectional_e2e.py # Transfer E2E validations
├── fav_coin/                      # Favorite coin configuration test suite
│   ├── conftest.py                # Shared fixtures for favorite coin tests
│   └── test_fav_coin_e2e.py       # Favorite coins E2E validations
├── config.py                      # Project configurations & fallback environment values
├── startup_cleanup.py             # Pre-test cleanup utility for positions, orders, and balances
├── pytest.ini                     # pytest markers, configurations, and test directories
└── requirements.txt               # Main Python dependencies
```

---

## 3. Test Execution Steps

Follow these sequential steps to prepare your environment and execute the test suites.

### Step 1: Environment Setup
Ensure you have the following installed on your machine:
*   **Python 3.8** or higher (Python 3.11 is recommended).
*   **Allure CLI** installed on your system path (required to generate and serve the visual test reports).

### Step 2: Create a Virtual Environment
Navigate to the `testing/` directory and spin up an isolated virtual environment:
```bash
python -m venv .venv
```

### Step 3: Activate Virtual Environment
*   **Windows (PowerShell):**
    ```powershell
    .venv\Scripts\Activate.ps1
    ```
*   **macOS / Linux:**
    ```bash
    source .venv/bin/activate
    ```

### Step 4: Install Dependencies
With the virtual environment active, install all required dependencies:
```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
You can configure behavior by setting the following environment variables (or rely on the defaults predefined in `config.py`):
*   `GIOTTUS_DEFAULT_CTID`: Default Customer ID (defaults to `"1686"`).
*   `GIOTTUS_BASE_SERVICE_URL`: Service Base URL (defaults to `"https://devtesting.giottus.com/service5010"`).
*   `GIOTTUS_FUTURES_SERVICE_URL`: Futures Service API URL (defaults to `"https://devtesting.giottus.com/service5031/api/v1/futures"`).

### Step 6: Execute the Pre-Test Cleanup Utility
Before executing any test suite, always run the startup script to clear the exchange account's active positions and orders. This ensures a predictable, clean state:
```bash
python startup_cleanup.py
```

### Step 7: Execute Test Suite
Run the test suites using `pytest`. You can run the entire directory or target individual components.

### Step 8: View Allure Reports
After running the tests with the `--alluredir` option, spin up a local server to visualize test results, execution steps, logs, and screenshots.

---

## 4. Commands Section

Quick-reference commands to manage and run the project:

### Dependency Installation
```bash
pip install -r requirements.txt
```

### Run Environment Preparation Utility
```bash
python startup_cleanup.py
```

### Run Entire Test Suite (Configured in pytest.ini)
```bash
pytest -v
```

### Run Entire Suite with Allure Result Generation
```bash
pytest --alluredir=allure-results
```

### Run Individual Test Modules
*   **Run Futures Limit positive scenarios:**
    ```bash
    pytest futures/futures_limit/positive/test_futures_limit_long.py -v
    ```
*   **Run Spot USDT test suite:**
    ```bash
    pytest spot/spot_usdt/positive/ -v
    ```
*   **Run bidirectional wallet transfers:**
    ```bash
    pytest wallet/test_asset_transfer_bidirectional_e2e.py -v
    ```

### Generate and Serve Allure Reports
*   **Serve report locally (Auto-opens in browser):**
    ```bash
    allure serve allure-results
    ```
*   **Generate static HTML report:**
    ```bash
    allure generate allure-results --clean -o allure-report
    ```

---

## 5. Notes Section

*   **Pre-test Wallet Balance Precondition:** E2E execution requires active spot and futures wallet balances. The `startup_cleanup.py` script automatically verifies both balances before execution. If a balance is non-positive, a warning is logged.
*   **Automatic Position & Order Sweeping:** Stranded positions or open orders lock account margins and conflict with subsequent test operations. Running `startup_cleanup.py` resolves this by executing market reduce-only orders to instantly close active positions and clean open orders.
*   **Serial Execution Marker:** Tests marked with `@pytest.mark.serial` must run sequentially to avoid state collisions when modifying shared user preferences or settings.
