"""HTTP client for Giottus Futures favorite coin pair endpoints."""

from __future__ import annotations

import logging
import re
from typing import Any

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import Config
LOGGER = logging.getLogger("giottus.futures")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False


class FuturesClient:
    """Small API client for managing favorite futures coin pairs."""

    BASE_URL = Config.GIOTTUS_FUTURES_SERVICE_URL
    _COINPAIR_PATTERN = re.compile(r"^[A-Z0-9]{2,20}/[A-Z0-9]{2,20}$")

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.verify = False
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def set_favorite_coin_pair(self, ctid: Any, coinpair: Any, value: Any) -> dict[str, Any]:
        """Add or remove a favorite coin pair."""

        ctid_error = self._validate_ctid(ctid)
        if ctid_error:
            return ctid_error

        coinpair_error = self._validate_coinpair(coinpair)
        if coinpair_error:
            return coinpair_error

        value_error = self._validate_value(value)
        if value_error:
            return value_error

        payload = {
            "ctid": str(ctid).strip(),
            "coinpair": str(coinpair).strip(),
            "value": str(value),
        }
        return self._request(
            "POST",
            "/set/favcoinpair",
            json=payload,
        )

    def get_favorite_coin_pairs(self, ctid: Any) -> dict[str, Any]:
        """Fetch the user's favorite futures coin pairs."""

        ctid_error = self._validate_ctid(ctid)
        if ctid_error:
            return ctid_error

        return self._request(
            "GET",
            "/favcoinpairs",
            params={"ctid": str(ctid).strip()},
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        debug_payload = kwargs.get("json") or kwargs.get("params") or {}
        LOGGER.info("Giottus request %s %s payload=%s", method, url, debug_payload)

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            LOGGER.error("Giottus request failed: %s", exc)
            return {
                "Status": "Failure",
                "Code": -1,
                "Message": f"Request failed: {exc}",
                "Data": [],
            }

        LOGGER.info(
            "Giottus response status=%s content-type=%s",
            response.status_code,
            response.headers.get("Content-Type", "unknown"),
        )
        return self._normalize_response(response)

    def _normalize_response(self, response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json() if response.text else {}
        except ValueError:
            LOGGER.error("Giottus response was not valid JSON: %s", response.text[:500])
            return {
                "Status": "Success" if response.ok else "Failure",
                "Code": 100 if response.ok else response.status_code,
                "Message": "Response was not valid JSON.",
                "Data": [],
                "HTTPStatusCode": response.status_code,
                "RawResponse": response.text[:500],
            }

        if isinstance(payload, dict):
            normalized = dict(payload)
        else:
            normalized = {
                "Data": payload,
            }

        normalized.setdefault("Status", "Success" if response.ok else "Failure")
        normalized.setdefault("Code", 100 if response.ok else response.status_code)
        normalized.setdefault("Data", normalized.get("Data", []))
        normalized["HTTPStatusCode"] = response.status_code

        LOGGER.info(
            "Giottus normalized response Status=%s Code=%s",
            normalized.get("Status"),
            normalized.get("Code"),
        )
        return normalized

    @staticmethod
    def _validate_ctid(ctid: Any) -> dict[str, Any] | None:
        ctid_value = "" if ctid is None else str(ctid).strip()
        if not ctid_value:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "CTID is required.",
                "Data": [],
            }
        if ctid_value == "REPLACE_WITH_VALID_CTID":
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": (
                    "DEFAULT_CTID is still set to the placeholder value. "
                    "Update config.py or set GIOTTUS_DEFAULT_CTID to a valid CTID."
                ),
                "Data": [],
            }
        return None

    @classmethod
    def _validate_coinpair(cls, coinpair: Any) -> dict[str, Any] | None:
        if coinpair is None:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Coin pair is required.",
                "Data": [],
            }

        coinpair_value = str(coinpair).strip()
        if not coinpair_value:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Coin pair cannot be empty.",
                "Data": [],
            }

        if not cls._COINPAIR_PATTERN.fullmatch(coinpair_value):
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Coin pair must be in SYMBOL/QUOTE format using uppercase letters and digits.",
                "Data": [],
            }
        return None

    @staticmethod
    def _validate_value(value: Any) -> dict[str, Any] | None:
        value_as_text = "" if value is None else str(value).strip()
        if value_as_text not in {"0", "1"}:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Value must be '0' to add or '1' to remove.",
                "Data": [],
            }
        return None

    @staticmethod
    def _validate_quantity(quantity: Any) -> dict[str, Any] | None:
        if quantity is None:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Quantity is required.",
                "Data": [],
            }

        quantity_value = str(quantity).strip()
        if not quantity_value:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Quantity cannot be empty.",
                "Data": [],
            }

        try:
            quantity_float = float(quantity_value)
        except ValueError:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Quantity must be a valid number.",
                "Data": [],
            }

        if quantity_float <= 0:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Quantity must be greater than zero.",
                "Data": [],
            }

        if "." in quantity_value and len(quantity_value.split(".")[1]) > 8:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Quantity exceeds 8 decimal places limit.",
                "Data": [],
            }
        return None

    @staticmethod
    def _validate_price(price: Any) -> dict[str, Any] | None:
        if price is None:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Price is required.",
                "Data": [],
            }

        price_value = str(price).strip()
        if not price_value:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Price cannot be empty.",
                "Data": [],
            }

        try:
            price_float = float(price_value)
        except ValueError:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Price must be a valid number.",
                "Data": [],
            }

        if price_float <= 0:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Price must be strictly positive.",
                "Data": [],
            }

        if "." in price_value and len(price_value.split(".")[1]) > 8:
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "Price exceeds 8 decimal places limit.",
                "Data": [],
            }
        return None

    def create_futures_order(self, ctid: Any, symbol: Any, order_side: Any, quantity: Any) -> dict[str, Any]:
        """Place a Futures market order (basic MARKET order payload).

        This mirrors the Spot client's basic validation and POST behaviour but
        targets the futures service base URL. The endpoint path may need
        adjustment depending on the real futures API path.
        """

        # basic validations (reuse existing validators where applicable)
        ctid_error = self._validate_ctid(ctid)
        if ctid_error:
            return ctid_error

        coinpair_error = self._validate_coinpair(symbol)
        if coinpair_error:
            return coinpair_error

        quantity_error = self._validate_quantity(quantity)
        if quantity_error:
            return quantity_error

        payload = {
            "ctid": str(ctid).strip(),
            "symbol": str(symbol).strip(),
            "order_type": "MARKET",
            "order_side": str(order_side).upper().strip(),
            "quantity": str(quantity).strip(),
        }

        return self._request("POST", "/order", json=payload)

    def create_futures_limit_order(
        self,
        ctid: Any,
        symbol: Any,
        order_side: Any,
        quantity: Any,
        price: Any,
    ) -> dict[str, Any]:
        """Place a Futures LIMIT order."""

        ctid_error = self._validate_ctid(ctid)
        if ctid_error:
            return ctid_error

        coinpair_error = self._validate_coinpair(symbol)
        if coinpair_error:
            return coinpair_error

        quantity_error = self._validate_quantity(quantity)
        if quantity_error:
            return quantity_error

        price_error = self._validate_price(price)
        if price_error:
            return price_error

        payload = {
            "ctid": str(ctid).strip(),
            "symbol": str(symbol).strip(),
            "order_type": "LIMIT",
            "order_side": str(order_side).upper().strip(),
            "quantity": str(quantity).strip(),
            "price": str(price).strip(),
        }

        return self._request("POST", "/order", json=payload)

    def transfer_spot_to_futures(self, ctid: Any, symbol: Any, qty: Any, transfer_type: int = 0) -> dict[str, Any]:
        """Transfer funds from spot wallet to futures wallet."""
        payload = {
            "ctid": str(ctid).strip(),
            "symbol": str(symbol).strip(),
            "qty": str(qty).strip(),
            "transfer_type": transfer_type,
        }
        return self._request("POST", "/fund/transfer", json=payload)

    def transfer_futures_to_spot(self, ctid: Any, symbol: Any, qty: Any, transfer_type: int = 1) -> dict[str, Any]:
        """Transfer funds from futures wallet to spot wallet."""
        payload = {
            "ctid": str(ctid).strip(),
            "symbol": str(symbol).strip(),
            "qty": str(qty).strip(),
            "transfer_type": transfer_type,
        }
        return self._request("POST", "/fund/transfer", json=payload)

    def fetch_user_details(self, ctid: Any, symbol: str = None) -> Any:
        params = {"ctid": str(ctid).strip()}
        if symbol:
            params["symbol"] = symbol
        resp = self._request("GET", "/user-details", params=params)

        # Track whether this was a real API error (Code != 100 or Status != Success)
        api_error = resp.get("Status") != "Success" or resp.get("Code") not in (100, None)

        # Guard against API returning an empty list for 'Data' on failure
        if "Data" not in resp or not isinstance(resp["Data"], dict):
            resp["Data"] = {
                "wallet_balance": {
                    "futures_wallet": {"asset": "USDT", "value": "0.0"},
                    "spot_wallet": {"asset": "USDT", "value": "0.0"},
                }
            }

        # Store the API error flag so callers can detect it
        resp["_api_error"] = api_error

        # Helper to enable dot access to dictionary fields
        class DotDict(dict):
            __getattr__ = dict.get
            __setattr__ = dict.__setitem__
            __delattr__ = dict.__delitem__

        def to_dotdict(d):
            if isinstance(d, dict):
                return DotDict({k: to_dotdict(v) for k, v in d.items()})
            elif isinstance(d, list):
                return [to_dotdict(vi) for vi in d]
            return d

        return to_dotdict(resp)

    def wait_for_balance_update(
        self,
        ctid: Any,
        symbol: Any,
        expected_futures_value: float,
        expected_spot_value: float,
        timeout_seconds: float = 30.0,
        poll_interval: float = 2.0,
    ) -> bool:
        """Poll user-details until balances match expected values or timeout.

        Returns False immediately after 3 consecutive API errors to avoid hanging
        when the user-details endpoint is unavailable in the test environment.
        """
        import time
        start_time = time.time()
        tolerance = 0.01
        consecutive_api_errors = 0
        MAX_API_ERRORS = 3  # Abort polling after this many consecutive errors

        while time.time() - start_time < timeout_seconds:
            details = self.fetch_user_details(ctid=ctid, symbol=symbol)

            # If the API itself is returning errors, abort rather than polling forever
            if details.get("_api_error"):
                consecutive_api_errors += 1
                LOGGER.warning(
                    "fetch_user_details returned an API error (%d/%d). "
                    "Status=%s Code=%s Msg=%s",
                    consecutive_api_errors,
                    MAX_API_ERRORS,
                    details.get("Status"),
                    details.get("Code"),
                    details.get("Msg"),
                )
                if consecutive_api_errors >= MAX_API_ERRORS:
                    LOGGER.error(
                        "Aborting balance polling after %d consecutive API errors. "
                        "The user-details endpoint may not support this CTID/symbol.",
                        MAX_API_ERRORS,
                    )
                    return False
                time.sleep(poll_interval)
                continue

            # Reset error counter on a successful response
            consecutive_api_errors = 0

            try:
                futures_val = float(details.Data.wallet_balance.futures_wallet.value)
                spot_val = float(details.Data.wallet_balance.spot_wallet.value)

                if (
                    abs(futures_val - expected_futures_value) < tolerance
                    and abs(spot_val - expected_spot_value) < tolerance
                ):
                    return True
            except Exception as e:
                LOGGER.error("Error reading balance fields: %s", e)

            time.sleep(poll_interval)

        return False

