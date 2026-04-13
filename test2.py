import httpx
import time

from config import Config
from models.futures_model.user_details_model import UserDetailsResponse
from models.futures_model.api_response_models import (
    TransferResponse,
    FavoriteCoinPairsResponse,
    CoinPairConfigResponse,
)

class FuturesClient:
    def __init__(self, token: str = ""):
        # token parameter reserved for future auth support; currently unused
        self.client = httpx.Client(
            base_url=Config.GIOTTUS_FUTURES_SERVICE_URL,
            timeout=30.0,
        )

    def transfer_spot_to_futures(self, ctid: int, symbol: str, qty: str, transfer_type: int = 0):
        """Transfer funds from spot wallet to futures wallet.
        
        Args:
            ctid: Client trading ID
            symbol: Currency symbol (e.g., 'INR', 'USDT')
            qty: Amount as string (e.g., '1.00')
            transfer_type: 0 for spot-to-futures
            
        Returns:
            Dictionary with Status and Code (validated via Pydantic)
        """
        payload = {
            "ctid": str(ctid),
            "qty": qty,
            "symbol": symbol,
            "transfer_type": transfer_type,
        }
        resp = self.client.post("fund/transfer", json=payload)
        resp.raise_for_status()
        # Validate response structure but return as dict for backward compatibility
        validated = TransferResponse.model_validate(resp.json())
        return validated.model_dump()

    def transfer_futures_to_spot(self, ctid: int, symbol: str, qty: str, transfer_type: int = 1):
        """Transfer funds from futures wallet to spot wallet.
        
        Args:
            ctid: Client trading ID
            symbol: Currency symbol (e.g., 'INR', 'USDT')
            qty: Amount as string (e.g., '1.00')
            transfer_type: 1 for futures-to-spot (default)
            
        Returns:
            Dictionary with Status and Code (validated via Pydantic)
        """
        payload = {
            "ctid": str(ctid),
            "qty": qty,
            "symbol": symbol,
            "transfer_type": transfer_type,
        }
        resp = self.client.post("fund/transfer", json=payload)
        resp.raise_for_status()
        # Validate response structure but return as dict for backward compatibility
        validated = TransferResponse.model_validate(resp.json())
        return validated.model_dump()

    def fetch_user_details(self, ctid: int, page: int = 1, page_size: int = 10, symbol: str = None):
        params = {
            "ctid": ctid,
            "page": page,
            "symbol": symbol,
            "page_size": page_size,
        }
        if symbol:
            params["symbol"] = symbol
        
        response = self.client.get("user-details", params=params)
        response.raise_for_status()
        # Automatically validate the response against our Pydantic model
        return UserDetailsResponse.model_validate(response.json())

    def wait_for_balance_update(
        self,
        ctid: int,
        symbol: str,
        expected_futures_value: float,
        expected_spot_value: float,
        timeout_seconds: float = 30.0,
        poll_interval: float = 2.0,
    ) -> bool:
        """Poll user-details until balances match expected values or timeout.
        
        Args:
            ctid: Client trading ID
            symbol: Trading symbol
            expected_futures_value: Expected futures wallet balance
            expected_spot_value: Expected spot wallet balance
            timeout_seconds: Max time to wait (default 30s)
            poll_interval: Time between polls (default 2s)
            
        Returns:
            True if balances updated within timeout, False otherwise
        """
        start_time = time.time()
        tolerance = 0.01  # Allow 0.01 difference due to rounding
        
        while time.time() - start_time < timeout_seconds:
            details = self.fetch_user_details(ctid=ctid, symbol=symbol)
            futures_val = float(details.Data.wallet_balance.futures_wallet.value)
            spot_val = float(details.Data.wallet_balance.spot_wallet.value)
            
            if (
                abs(futures_val - expected_futures_value) < tolerance
                and abs(spot_val - expected_spot_value) < tolerance
            ):
                return True
            
            time.sleep(poll_interval)
        
        return False
    def set_favorite_coin_pair(self, ctid: str, coinpair: str, value: int) -> dict:
        """Set or remove a favorite coin pair for a user.
        
        Args:
            ctid: Client trading ID
            coinpair: Coin pair symbol (e.g., 'BTC/USDT')
            value: 0 to add as favorite, 1 to remove from favorites
            
        Returns:
            Dictionary with Status and Code (validated via Pydantic)
        """
        payload = {
            "ctid": str(ctid),
            "coinpair": coinpair,
            "value": value,
        }
        resp = self.client.post("set/favcoinpair", json=payload)
        resp.raise_for_status()
        # Validate response structure but return as dict for backward compatibility
        validated = FavoriteCoinPairsResponse.model_validate(resp.json())
        return validated.model_dump()

    def get_favorite_coin_pairs(self, ctid: str) -> dict:
        """Retrieve list of favorite coin pairs for a user.
        
        Args:
            ctid: Client trading ID
            
        Returns:
            Dictionary containing list of favorite coin pairs in Data field (validated via Pydantic)
        """
        params = {
            "ctid": str(ctid),
        }
        resp = self.client.get("favcoinpairs", params=params)
        resp.raise_for_status()
        # Validate response structure but return as dict for backward compatibility
        validated = FavoriteCoinPairsResponse.model_validate(resp.json())
        return validated.model_dump()

    def get_coin_pair_config(self) -> dict:
        """Retrieve complete coin pair trading configuration.
        
        Returns comprehensive configuration including:
        - symbol_config: Trading parameters for all symbols
        - currency_config: Currency-specific settings
        - ticker_data: Current market data
        - mark_price_data: Mark prices and funding rates
        
        Returns:
            Dictionary with Status, Code, Msg, and Data sections (validated via Pydantic)
        """
        resp = self.client.get("config")
        resp.raise_for_status()
        # Validate response structure but return as dict for backward compatibility
        validated = CoinPairConfigResponse.model_validate(resp.json())
        return validated.model_dump()

    # ========================================================================
    # ORDER MANAGEMENT METHODS
    # ========================================================================

    def create_order(self, ctid: int, symbol: str, qty: str, price: str, amount: str, order_type: str,
                     order_side: str, leverage: str = "1", reduce_only: str = "0",
                     sl_price: str = None, tp_price: str = None) -> dict:
        """Create a futures order (buy long, sell short, limit, market, etc).
        
        Args:
            ctid: Client trading ID
            symbol: Trading symbol (e.g., 'BTC/USDT')
            qty: Order quantity as string
            price: Order price as string
            amount: Order amount as string
            order_type: Order type (0=Market, 1=Limit, 10=Limit TPSL, 11=TP Market, 12=SL Market)
            order_side: Order side (0=Long, 1=Short)
            leverage: Leverage to use (1-50 depending on symbol)
            reduce_only: 0 = normal order, 1 = reduce only (close position)
            sl_price: Stop loss price (optional)
            tp_price: Take profit price (optional)
            
        Returns:
            Dictionary with order creation response including order ID
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
        if sl_price:
            payload["sl_price"] = sl_price
        if tp_price:
            payload["tp_price"] = tp_price
        
        resp = self.client.post("order", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_active_positions(self, ctid: int, page: int = 1, page_size: int = 20) -> dict:
        """Retrieve active positions for a user.
        
        Args:
            ctid: Client trading ID
            page: Page number for pagination
            page_size: Number of records per page
            
        Returns:
            Dictionary with list of active positions
        """
        params = {"ctid": ctid, "page": page, "page_size": page_size}
        resp = self.client.get("position", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_order_history(self, ctid: int, page: int = 1, page_size: int = 10) -> dict:
        """Retrieve order history.
        
        Args:
            ctid: Client trading ID
            page: Page number for pagination
            page_size: Number of records per page
            
        Returns:
            Dictionary with order history
        """
        params = {"ctid": ctid, "page": page, "page_size": page_size}
        resp = self.client.get("order", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_trade_history(self, ctid: int, page: int = 1, page_size: int = 20) -> dict:
        """Retrieve trade history.
        
        Args:
            ctid: Client trading ID
            page: Page number
            page_size: Number of records per page
            
        Returns:
            Dictionary with trade history
        """
        params = {"ctid": ctid, "page": page, "page_size": page_size}
        resp = self.client.get("trade/history", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_wallet_transactions(self, ctid: int, page: int = 1, page_size: int = 20) -> dict:
        """Retrieve wallet transaction history.
        
        Args:
            ctid: Client trading ID
            page: Page number
            page_size: Number of records per page
            
        Returns:
            Dictionary with wallet transactions
        """
        params = {"ctid": ctid, "page": page, "page_size": page_size}
        resp = self.client.get("wallet/transactions", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_open_orders(self, ctid: int, page: int = 1, page_size: int = 10) -> dict:
        """Retrieve open orders.
        
        Args:
            ctid: Client trading ID
            page: Page number
            page_size: Number of records per page
            
        Returns:
            Dictionary with open orders
        """
        params = {"ctid": ctid, "page": page, "page_size": page_size}
        resp = self.client.get("open-order", params=params)
        resp.raise_for_status()
        return resp.json()

    def cancel_order(self, ctid: int, order_id: str) -> dict:
        """Cancel an open order.
        
        Args:
            ctid: Client trading ID
            order_id: Order ID to cancel
            
        Returns:
            Dictionary with cancellation response
        """
        payload = {"ctid": ctid, "order_id": order_id}
        resp = self.client.post("cancel-order", json=payload)
        resp.raise_for_status()
        return resp.json()

    def close_position(self, ctid: int, position_id: str, qty: str = None) -> dict:
        """Close a position or reduce it.
        
        Args:
            ctid: Client trading ID
            position_id: Position ID to close
            qty: Quantity to close (optional, if not set closes entire position)
            
        Returns:
            Dictionary with close response
        """
        payload = {"ctid": ctid, "position_id": position_id}
        if qty:
            payload["qty"] = qty
        resp = self.client.post("close-position", json=payload)
        resp.raise_for_status()
        return resp.json()

    def adjust_leverage(self, ctid: int, symbol: str, leverage: int) -> dict:
        """Adjust leverage for a symbol.
        
        Args:
            ctid: Client trading ID
            symbol: Trading symbol (e.g., 'BTC/USDT')
            leverage: New leverage value
            
        Returns:
            Dictionary with adjustment response
        """
        payload = {"ctid": ctid, "symbol": symbol, "leverage": leverage}
        resp = self.client.post("adjust-leverage", json=payload)
        resp.raise_for_status()
        return resp.json()

    def view_tpsl_orders(self, ctid: int, symbol: str) -> dict:
        """View take profit/stop loss orders for a symbol.
        
        Args:
            ctid: Client trading ID
            symbol: Trading symbol
            
        Returns:
            Dictionary with TP/SL orders
        """
        params = {"ctid": ctid, "symbol": symbol}
        resp = self.client.get("view/tpsl", params=params)
        resp.raise_for_status()
        return resp.json()

    # ========================================================================
    # MARKET DATA METHODS (Futures Only)
    # ========================================================================

    def get_ticker(self) -> dict:
        """Retrieve current ticker data for all trading pairs.
        
        Returns:
            Dictionary with ticker data
        """
        resp = self.client.get("ticker")
        resp.raise_for_status()
        return resp.json()

    def get_mark_price(self, symbol: str = None) -> dict:
        """Retrieve mark price and funding rate information.
        
        Args:
            symbol: Trading symbol (optional, gets all if not provided)
            
        Returns:
            Dictionary with mark price data
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        resp = self.client.get("mark-price", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_public_trade_history(self, symbol: str = None) -> dict:
        """Retrieve public trade history for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with public trades
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        resp = self.client.get("trade-history", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_user_trades(self, ctid: int, page: int = 1, page_size: int = 10) -> dict:
        """Retrieve user's personal trade history (futures).
        
        Args:
            ctid: Client trading ID
            page: Page number
            page_size: Records per page
            
        Returns:
            Dictionary with user trades
        """
        params = {"ctid": ctid, "page": page, "page_size": page_size}
        resp = self.client.get("user-trades", params=params)
        resp.raise_for_status()
        return resp.json()

    def update_tpsl_order(self, ctid: int, symbol: str, tp_qty: str = None, 
                         tp_price: str = None, sl_qty: str = None, 
                         sl_price: str = None) -> dict:
        """Update take profit/stop loss orders for a position.
        
        Args:
            ctid: Client trading ID
            symbol: Trading symbol
            tp_qty: Take profit quantity
            tp_price: Take profit price
            sl_qty: Stop loss quantity
            sl_price: Stop loss price
            
        Returns:
            Dictionary with update response
        """
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

    def adjust_position(self, ctid: int, symbol: str, liquidation_price: str = None, 
                       adjust_type: int = None) -> dict:
        """Adjust position settings (liquidation price, type, etc).
        
        Args:
            ctid: Client trading ID
            symbol: Trading symbol
            liquidation_price: New liquidation price
            adjust_type: Adjustment type
            
        Returns:
            Dictionary with adjustment response
        """
        payload = {"ctid": ctid, "symbol": symbol}
        if liquidation_price:
            payload["liquidation_price"] = liquidation_price
        if adjust_type is not None:
            payload["type"] = adjust_type
        
        resp = self.client.post("adjust-position", json=payload)
        resp.raise_for_status()
        return resp.json()