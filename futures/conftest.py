"""
Futures test configuration and shared helpers.

This file keeps the project root importable and records what happened during the
best-effort pre-suite cleanup. The backend currently reports the cancel endpoint
as disabled in dev, so tests should surface that condition clearly instead of
silently skipping when the shared account hits the per-symbol order cap.
"""

import os
import sys

import pytest
from futures.test_support import FUTURES_CLEANUP_STATE


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(scope="session", autouse=True)
def cancel_all_open_orders_before_suite():
    """Best-effort cleanup for shared-account futures E2E tests."""
    from config import Config
    from clients.futures_trading_client import FuturesTradingClient

    client = FuturesTradingClient()
    FUTURES_CLEANUP_STATE["attempted"] = True

    try:
        resp = client.get_open_orders(ctid=Config.DEFAULT_CTID, page_size=50)
        orders = resp.get("Data") or []
        if isinstance(orders, list):
            FUTURES_CLEANUP_STATE["open_order_count"] = len(orders)
            for order in orders:
                oid = order.get("order_id") or order.get("id")
                if oid:
                    FUTURES_CLEANUP_STATE["cancel_attempt_count"] += 1
                    cancel_response = client.cancel_order(
                        ctid=Config.DEFAULT_CTID,
                        order_id=str(oid),
                    )
                    if cancel_response.get("Status") != "Success":
                        FUTURES_CLEANUP_STATE["cancel_failures"].append(cancel_response)
    except Exception as exc:
        FUTURES_CLEANUP_STATE["exception"] = repr(exc)

    yield
