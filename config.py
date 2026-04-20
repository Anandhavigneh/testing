"""Project configuration for the Giottus Futures E2E suite."""

from __future__ import annotations

import os

# TODO: Replace this placeholder with a valid CTID, or set GIOTTUS_DEFAULT_CTID.
DEFAULT_CTID = os.getenv("GIOTTUS_DEFAULT_CTID", "1529")
# Symbol used for user-details / balance queries (spot side uses simple asset symbol)
DEFAULT_SYMBOL = os.getenv("GIOTTUS_DEFAULT_SYMBOL", "BTC/USDT")
# Symbol used for fund-transfer calls (futures trading pair)
DEFAULT_FUTURES_SYMBOL = os.getenv("GIOTTUS_DEFAULT_FUTURES_SYMBOL", "USDT")
COINPAIR_BTC_USDT = "BTC/USDT"
COINPAIR_ETH_USDT = "ETH/USDT"

GIOTTUS_BASE_SERVICE_URL = os.getenv("GIOTTUS_BASE_SERVICE_URL", "https://devtesting.giottus.com/service5010")
GIOTTUS_FUTURES_SERVICE_URL = os.getenv("GIOTTUS_FUTURES_SERVICE_URL", "https://devtesting.giottus.com/service5031/api/v1/futures")

class Config:
    """Compatibility wrapper expected by the existing tests."""

    DEFAULT_CTID = DEFAULT_CTID
    DEFAULT_SYMBOL = DEFAULT_SYMBOL
    DEFAULT_FUTURES_SYMBOL = DEFAULT_FUTURES_SYMBOL
    COINPAIR_BTC_USDT = COINPAIR_BTC_USDT
    COINPAIR_ETH_USDT = COINPAIR_ETH_USDT
    GIOTTUS_BASE_SERVICE_URL = GIOTTUS_BASE_SERVICE_URL
    GIOTTUS_FUTURES_SERVICE_URL = GIOTTUS_FUTURES_SERVICE_URL
