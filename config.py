"""Project configuration for the Giottus Futures E2E suite."""

from __future__ import annotations

import os

# TODO: Replace this placeholder with a valid CTID, or set GIOTTUS_DEFAULT_CTID.
DEFAULT_CTID = os.getenv("GIOTTUS_DEFAULT_CTID", "1686")
COINPAIR_BTC_USDT = "BTC/USDT"
COINPAIR_ETH_USDT = "ETH/USDT"

GIOTTUS_BASE_SERVICE_URL = os.getenv("GIOTTUS_BASE_SERVICE_URL", "https://devtesting.giottus.com/service5010")
GIOTTUS_FUTURES_SERVICE_URL = os.getenv("GIOTTUS_FUTURES_SERVICE_URL", "https://devtesting.giottus.com/service5031/api/v1/futures")
print(f"Using GIOTTUS_BASE_SERVICE_URL: {GIOTTUS_BASE_SERVICE_URL}")
class Config:
    """Compatibility wrapper expected by the existing tests."""

    DEFAULT_CTID = DEFAULT_CTID
    DEFAULT_SYMBOL = "USDT"
    DEFAULT_FUTURES_SYMBOL = "USDT"
    COINPAIR_BTC_USDT = COINPAIR_BTC_USDT
    COINPAIR_ETH_USDT = COINPAIR_ETH_USDT
    GIOTTUS_BASE_SERVICE_URL = GIOTTUS_BASE_SERVICE_URL
    GIOTTUS_FUTURES_SERVICE_URL = GIOTTUS_FUTURES_SERVICE_URL
