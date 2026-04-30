"""
futures_trading_client.py — Standalone FuturesClient for E2E order management tests.

This client handles all futures trading operations (orders, positions, leverage)
using httpx. It has NO dependency on Pydantic models, making it self-contained
and importable from any test subdirectory.
"""
import httpx
from config import Config


class FuturesTradingClient:
    """Lightweight futures client for E2E tests — order management focused."""

    def __init__(self):
        self.client = httpx.Client(
            base_url=Config.GIOTTUS_FUTURES_SERVICE_URL,
            timeout=30.0,
            verify=False
        )

    # =========================================================================
    # ORDER MANAGEMENT
    # =========================================================================

    def create_order(self, ctid: int, symbol: str, qty: str, price: str,
                     amount: str, order_type: str, order_side: str,
                     leverage: str = "1", reduce_only: str = "0",
                     sl_price: str = None, tp_price: str = None) -> dict:
        """Create a futures order (Market/Limit, Long/Short).

        Args:
            ctid:        Client trading ID
            symbol:      Trading symbol e.g. 'BTC/USDT'
            qty:         Quantity as string
            price:       Price as string ('0' for Market orders)
            amount:      Amount as string
            order_type:  '0'=Market, '1'=Limit
            order_side:  '0'=Long (Buy), '1'=Short (Sell)
            leverage:    Leverage multiplier string (default '1')
            reduce_only: '0'=normal, '1'=close-only
            sl_price:    Stop-loss price (optional)
            tp_price:    Take-profit price (optional)
        """
        payload = {
            "ctid": ctid,
            "symbol": symbol,
            "qty": qty,
            "price": price,
            "order_type": order_type,
            "order_side": order_side,
            "leverage": leverage,
            "reduce_only": reduce_only,
            "amount": amount,
        }
        if sl_price is not None:
            payload["sl_price"] = sl_price
        if tp_price is not None:
            payload["tp_price"] = tp_price

        resp = self.client.post("order", json=payload)
        resp.raise_for_status()
        return resp.json()

    def cancel_order(self, ctid: int, order_id: str) -> dict:
        """Cancel an open futures order."""
        payload = {"ctid": ctid, "order_id": order_id}
        resp = self.client.post("cancel-order", json=payload)
        resp.raise_for_status()
        return resp.json()

    def close_position(self, ctid: int, position_id: str, qty: str = None) -> dict:
        """Close an active futures position (full or partial)."""
        payload = {"ctid": ctid, "position_id": position_id}
        if qty:
            payload["qty"] = qty
        resp = self.client.post("close-position", json=payload)
        resp.raise_for_status()
        return resp.json()

    def adjust_leverage(self, ctid: int, symbol: str, leverage: int) -> dict:
        """Set leverage for a symbol."""
        payload = {"ctid": ctid, "symbol": symbol, "leverage": leverage}
        resp = self.client.post("adjust-leverage", json=payload)
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # READ-ONLY QUERIES
    # =========================================================================

    def get_active_positions(self, ctid: int, page: int = 1, page_size: int = 20) -> dict:
        """Retrieve active positions."""
        params = {"ctid": ctid, "page": page, "page_size": page_size}
        resp = self.client.get("position", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_open_orders(self, ctid: int, page: int = 1, page_size: int = 10) -> dict:
        """Retrieve open (pending) orders."""
        params = {"ctid": ctid, "page": page, "page_size": page_size}
        resp = self.client.get("open-order", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_order_history(self, ctid: int, page: int = 1, page_size: int = 10) -> dict:
        """Retrieve past order history."""
        params = {"ctid": ctid, "page": page, "page_size": page_size}
        resp = self.client.get("order", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_trade_history(self, ctid: int, page: int = 1, page_size: int = 20) -> dict:
        """Retrieve past trade history."""
        params = {"ctid": ctid, "page": page, "page_size": page_size}
        resp = self.client.get("trade/history", params=params)
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # TPSL MANAGEMENT
    # =========================================================================

    def update_tpsl_order(self, ctid: int, symbol: str, tp_qty: str = None, 
                         tp_price: str = None, sl_qty: str = None, 
                         sl_price: str = None) -> dict:
        """Update take profit/stop loss orders for an active position."""
        payload = {"ctid": ctid, "symbol": symbol}
        if tp_qty:
            payload["tp_qty"] = tp_qty
        if tp_price:
            payload["tp_price"] = tp_price
        if sl_qty:
            payload["sl_qty"] = sl_qty
        if sl_price:
            payload["sl_price"] = sl_price
        
        resp = self.client.post("tpsl/order", json=payload)
        resp.raise_for_status()
        return resp.json()

    def view_tpsl_orders(self, ctid: int, symbol: str) -> dict:
        """View take profit/stop loss orders for a symbol."""
        params = {"ctid": ctid, "symbol": symbol}
        resp = self.client.get("view/tpsl", params=params)
        resp.raise_for_status()
        return resp.json()
