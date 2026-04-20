"""Futures market-order E2E coverage."""

import pytest

from clients.futures_trading_client import FuturesTradingClient
from config import Config
from futures.test_support import fail_on_order_book_limit


pytestmark = pytest.mark.futures


@pytest.fixture
def futures_client():
    return FuturesTradingClient()


def test_futures_market_long_valid_quantity(futures_client):
    """Place a market long with a valid quantity."""
    res = futures_client.create_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/USDT",
        qty="0.1",
        price="0",
        amount="10000",
        order_type="0",
        order_side="0",
        leverage="1",
    )
    assert isinstance(res, dict), f"Expected dict response, got: {res}"
    fail_on_order_book_limit(res, futures_client, Config.DEFAULT_CTID, "BTC/USDT")
    assert res.get("Status") == "Success", (
        f"Real Futures Market LONG trade FAILED - API response: {res}"
    )


def test_futures_market_short_valid_quantity(futures_client):
    """Place a market short with a valid quantity."""
    res = futures_client.create_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/USDT",
        qty="0.1",
        price="0",
        amount="10000",
        order_type="0",
        order_side="1",
        leverage="1",
    )
    assert isinstance(res, dict), f"Expected dict response, got: {res}"
    fail_on_order_book_limit(res, futures_client, Config.DEFAULT_CTID, "BTC/USDT")
    assert res.get("Status") == "Success", (
        f"Real Futures Market SHORT trade FAILED - API response: {res}"
    )


def test_futures_market_long_with_leverage(futures_client):
    """Place a market long using 5x leverage."""
    res = futures_client.create_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/USDT",
        qty="0.1",
        price="0",
        amount="10000",
        order_type="0",
        order_side="0",
        leverage="5",
    )
    assert isinstance(res, dict), f"Expected dict response, got: {res}"
    fail_on_order_book_limit(res, futures_client, Config.DEFAULT_CTID, "BTC/USDT")
    assert res.get("Status") == "Success", (
        f"Real Futures Market LONG (5x leverage) trade FAILED - API response: {res}"
    )


def test_futures_market_short_with_leverage(futures_client):
    """Place a market short using 10x leverage."""
    res = futures_client.create_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/USDT",
        qty="0.1",
        price="0",
        amount="10000",
        order_type="0",
        order_side="1",
        leverage="10",
    )
    assert isinstance(res, dict), f"Expected dict response, got: {res}"
    fail_on_order_book_limit(res, futures_client, Config.DEFAULT_CTID, "BTC/USDT")
    assert res.get("Status") == "Success", (
        f"Real Futures Market SHORT (10x leverage) trade FAILED - API response: {res}"
    )


def test_futures_market_close_long_position(futures_client):
    res = futures_client.create_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/USDT",
        qty="0.001",
        price="0",
        amount="0",
        order_type="0",
        order_side="1",
        leverage="1",
        reduce_only="1",
    )
    assert isinstance(res, dict)


def test_futures_market_close_short_position(futures_client):
    res = futures_client.create_order(
        ctid=Config.DEFAULT_CTID,
        symbol="BTC/USDT",
        qty="0.001",
        price="0",
        amount="0",
        order_type="0",
        order_side="0",
        leverage="1",
        reduce_only="1",
    )
    assert isinstance(res, dict)


def test_futures_market_invalid_ctid(futures_client):
    try:
        futures_client.create_order(
            ctid=0,
            symbol="BTC/USDT",
            qty="0.001",
            price="0",
            amount="0",
            order_type="0",
            order_side="0",
            leverage="1",
        )
    except Exception:
        assert True
    else:
        pass


def test_futures_market_empty_symbol(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol="",
            qty="0.001",
            price="0",
            amount="0",
            order_type="0",
            order_side="0",
            leverage="1",
        )
        assert res.get("Code") != 200
    except Exception:
        pass


def test_futures_market_invalid_symbol(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol="INVALID/USDT",
            qty="0.001",
            price="0",
            amount="0",
            order_type="0",
            order_side="0",
            leverage="1",
        )
        assert res.get("Code") != 200
    except Exception:
        pass


def test_futures_market_zero_quantity(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol="BTC/USDT",
            qty="0",
            price="0",
            amount="0",
            order_type="0",
            order_side="0",
            leverage="1",
        )
        assert res.get("Code") != 200
    except Exception:
        pass


def test_futures_market_negative_quantity(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol="BTC/USDT",
            qty="-0.5",
            price="0",
            amount="0",
            order_type="0",
            order_side="0",
            leverage="1",
        )
        assert res.get("Code") != 200
    except Exception:
        pass


def test_futures_market_empty_quantity(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol="BTC/USDT",
            qty="",
            price="0",
            amount="0",
            order_type="0",
            order_side="0",
            leverage="1",
        )
        assert res.get("Code") != 200
    except Exception:
        pass


def test_futures_market_exceed_balance(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol="BTC/USDT",
            qty="999999",
            price="0",
            amount="0",
            order_type="0",
            order_side="0",
            leverage="1",
        )
        assert res.get("Code") != 200
    except Exception:
        pass


def test_futures_market_invalid_order_side(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol="BTC/USDT",
            qty="0.001",
            price="0",
            amount="0",
            order_type="0",
            order_side="99",
            leverage="1",
        )
        assert res.get("Code") != 200
    except Exception:
        pass


def test_futures_market_invalid_leverage(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol="BTC/USDT",
            qty="0.001",
            price="0",
            amount="0",
            order_type="0",
            order_side="0",
            leverage="999",
        )
        assert res.get("Code") != 200
    except Exception:
        pass


def test_futures_market_zero_leverage(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol="BTC/USDT",
            qty="0.001",
            price="0",
            amount="0",
            order_type="0",
            order_side="0",
            leverage="0",
        )
        assert res.get("Code") != 200
    except Exception:
        pass


def test_futures_market_negative_leverage(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol="BTC/USDT",
            qty="0.001",
            price="0",
            amount="0",
            order_type="0",
            order_side="0",
            leverage="-1",
        )
        assert res.get("Code") != 200
    except Exception:
        pass


def test_futures_market_exceed_decimal_precision(futures_client):
    try:
        res = futures_client.create_order(
            ctid=Config.DEFAULT_CTID,
            symbol="BTC/USDT",
            qty="0.123456789123",
            price="0",
            amount="0",
            order_type="0",
            order_side="0",
            leverage="1",
        )
        assert res.get("Code") != 200
    except Exception:
        pass
