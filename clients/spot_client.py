import logging
import re
from typing import Any
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from config import Config

LOGGER = logging.getLogger("giottus.spot")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False

class SpotClient:
    """API client for executing Spot market orders."""

    # We use the base URL from config (Fallback locally)
    BASE_URL = Config.GIOTTUS_BASE_SERVICE_URL
    _COINPAIR_PATTERN = re.compile(r"^[A-Z0-9]{2,20}/[A-Z0-9]{2,20}$")

    def __init__(self, base_url: str | None = None, timeout: int = 30) -> None:
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def create_spot_order(self, ctid: Any, symbol: Any, order_side: Any, quantity: Any) -> dict[str, Any]:
        """Place a Spot market order."""
        
        # Validation checks locally
        ctid_error = self._validate_ctid(ctid)
        if ctid_error: return ctid_error

        symbol_error = self._validate_coinpair(symbol)
        if symbol_error: return symbol_error

        quantity_error = self._validate_quantity(quantity)
        if quantity_error: return quantity_error

        # Prepare Payload
        payload = {
            "ctid": str(ctid).strip(),
            "symbol": str(symbol).strip(),
            "order_type": "MARKET",
            "order_side": str(order_side).upper().strip(),
            "quantity": str(quantity).strip(),
        }

        # NOTE TO USER: Update this endpoint string if the Spot URL path is different
        return self._request("POST", "/api/v1/spot/order", json=payload)

    def create_spot_limit_order(self, ctid: Any, symbol: Any, order_side: Any, quantity: Any, price: Any) -> dict[str, Any]:
        """Place a Spot LIMIT order."""
        
        # Validation checks locally
        ctid_error = self._validate_ctid(ctid)
        if ctid_error: return ctid_error

        symbol_error = self._validate_coinpair(symbol)
        if symbol_error: return symbol_error

        quantity_error = self._validate_quantity(quantity)
        if quantity_error: return quantity_error

        price_error = self._validate_price(price)
        if price_error: return price_error

        # Prepare Payload
        payload = {
            "ctid": str(ctid).strip(),
            "symbol": str(symbol).strip(),
            "order_type": "LIMIT",
            "order_side": str(order_side).upper().strip(),
            "quantity": str(quantity).strip(),
            "price": str(price).strip(),
        }

        # Uses identical spot endpoint for creation
        return self._request("POST", "/api/v1/spot/order", json=payload)

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        LOGGER.info("Giottus request %s %s", method, url)
        try:
            response = self.session.request(method=method, url=url, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            LOGGER.error("Giottus request failed: %s", exc)
            return {"Status": "Failure", "Code": -1, "Message": f"Request failed: {exc}", "Data": []}
        return self._normalize_response(response)

    def _normalize_response(self, response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json() if response.text else {}
        except ValueError:
            return {"Status": "Failure", "Code": response.status_code, "Message": "Response not JSON"}
        
        normalized = dict(payload) if isinstance(payload, dict) else {"Data": payload}
        normalized.setdefault("Status", "Success" if response.ok else "Failure")
        normalized.setdefault("Code", 100 if response.ok else response.status_code)
        return normalized

    @staticmethod
    def _validate_ctid(ctid: Any) -> dict[str, Any] | None:
        if not ctid or not str(ctid).strip():
            return {"Status": "Failure", "Code": 400, "Message": "CTID is required."}
        return None

    @classmethod
    def _validate_coinpair(cls, symbol: Any) -> dict[str, Any] | None:
        if not symbol or not str(symbol).strip():
            return {"Status": "Failure", "Code": 400, "Message": "Symbol cannot be empty."}
        if not cls._COINPAIR_PATTERN.fullmatch(str(symbol).strip()):
            return {"Status": "Failure", "Code": 400, "Message": "Symbol must be in SYMBOL/QUOTE format."}
        return None

    @staticmethod
    def _validate_quantity(quantity: Any) -> dict[str, Any] | None:
        if quantity is None:
            return {"Status": "Failure", "Code": 400, "Message": "Quantity is required."}
        
        qty_str = str(quantity).strip()
        if not qty_str:
            return {"Status": "Failure", "Code": 400, "Message": "Quantity cannot be empty."}
        
        try:
            qty_float = float(qty_str)
            if qty_float <= 0:
                return {"Status": "Failure", "Code": 400, "Message": "Quantity must be greater than zero."}
            
            # Decimal tracking (simulating precision limits)
            if "." in qty_str and len(qty_str.split(".")[1]) > 8:
                return {"Status": "Failure", "Code": 400, "Message": "Quantity exceeds 8 decimal places limit."}
        except ValueError:
            return {"Status": "Failure", "Code": 400, "Message": "Quantity must be a valid number."}
        
        return None

    @staticmethod
    def _validate_price(price: Any) -> dict[str, Any] | None:
        if price is None:
            return {"Status": "Failure", "Code": 400, "Message": "Price is required."}
        
        price_str = str(price).strip()
        if not price_str:
            return {"Status": "Failure", "Code": 400, "Message": "Price cannot be empty."}
        
        try:
            price_float = float(price_str)
            if price_float <= 0:
                return {"Status": "Failure", "Code": 400, "Message": "Price must be strictly positive."}
                
            # Usually prices have strict tick sizes/decimals depending on the pair.
            # Assuming max 8 decimals similarly:
            if "." in price_str and len(price_str.split(".")[1]) > 8:
                return {"Status": "Failure", "Code": 400, "Message": "Price exceeds 8 decimal places limit."}
        except ValueError:
            return {"Status": "Failure", "Code": 400, "Message": "Price must be a valid number."}
        
        return None
