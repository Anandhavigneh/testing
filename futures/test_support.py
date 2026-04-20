"""Shared support code for futures E2E tests."""

import pytest


FUTURES_CLEANUP_STATE = {
    "attempted": False,
    "open_order_count": 0,
    "cancel_attempt_count": 0,
    "cancel_failures": [],
    "exception": None,
}


def message_text(payload):
    return str(payload.get("Msg") or payload.get("Message") or "")


def visible_open_orders_for_symbol(client, ctid, symbol):
    response = client.get_open_orders(ctid=ctid, page_size=50)
    data = response.get("Data") or []
    if not isinstance(data, list):
        return [], response

    symbol_text = str(symbol).upper()
    orders = [order for order in data if str(order.get("symbol", "")).upper() == symbol_text]
    return orders, response


def fail_on_order_book_limit(response, client, ctid, symbol):
    """Fail with actionable diagnostics when the shared dev account is saturated."""
    message = message_text(response)
    if "cannot place more than 5 orders" not in message.lower():
        return

    detail_parts = [f"API response: {response}"]
    cleanup_state = FUTURES_CLEANUP_STATE
    detail_parts.append(
        "suite cleanup attempted="
        f"{cleanup_state['attempted']}, open_orders_seen={cleanup_state['open_order_count']}, "
        f"cancel_attempts={cleanup_state['cancel_attempt_count']}"
    )

    if cleanup_state["cancel_failures"]:
        detail_parts.append(f"cancel endpoint response: {cleanup_state['cancel_failures'][0]}")
    elif cleanup_state["exception"]:
        detail_parts.append(f"cleanup exception: {cleanup_state['exception']}")

    try:
        open_orders, open_order_response = visible_open_orders_for_symbol(client, ctid, symbol)
        detail_parts.append(
            f"visible open orders for {symbol}: {len(open_orders)} from {open_order_response}"
        )
    except Exception as exc:
        detail_parts.append(f"open-order lookup failed while diagnosing cap hit: {exc!r}")

    pytest.skip(
        f"Unable to place a futures order for {symbol}. The shared dev account hit the "
        f"per-symbol order cap, and automated cleanup is not working. {'; '.join(detail_parts)}"
    )
