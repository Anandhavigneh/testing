"""HTTP client for Giottus Futures favorite coin pair endpoints."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests

from config import Config
from models.order_model import UserDetailsResponse
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

    # -----------------------------------------------------------------------
    # Fund-transfer methods
    # -----------------------------------------------------------------------

    def transfer_spot_to_futures(
        self,
        ctid: Any,
        symbol: Any,
        qty: Any,
        transfer_type: int = 0,
    ) -> dict[str, Any]:
        """Transfer funds from the spot wallet to the futures wallet.

        Args:
            ctid:          Client trading ID.
            symbol:        Currency / trading pair symbol.
            qty:           Amount to transfer (string, e.g. '1.00').
            transfer_type: 0 = spot → futures (default).

        Returns:
            Dict with at least ``Status`` and ``Code`` keys.
        """
        ctid_error = self._validate_ctid(ctid)
        if ctid_error:
            return ctid_error

        qty_error = self._validate_quantity(qty)
        if qty_error:
            return qty_error

        transfer_type_error = self._validate_transfer_type(transfer_type)
        if transfer_type_error:
            return transfer_type_error

        payload = {
            "ctid": str(ctid).strip(),
            "qty": str(qty).strip(),
            "symbol": str(symbol).strip() if symbol is not None else "",
            "transfer_type": transfer_type,
        }
        return self._request("POST", "/fund/transfer", json=payload)

    def transfer_futures_to_spot(
        self,
        ctid: Any,
        symbol: Any,
        qty: Any,
        transfer_type: int = 1,
    ) -> dict[str, Any]:
        """Transfer funds from the futures wallet back to the spot wallet.

        Args:
            ctid:          Client trading ID.
            symbol:        Currency / trading pair symbol.
            qty:           Amount to transfer (string, e.g. '1.00').
            transfer_type: 1 = futures → spot (default).

        Returns:
            Dict with at least ``Status`` and ``Code`` keys.
        """
        ctid_error = self._validate_ctid(ctid)
        if ctid_error:
            return ctid_error

        qty_error = self._validate_quantity(qty)
        if qty_error:
            return qty_error

        transfer_type_error = self._validate_transfer_type(transfer_type)
        if transfer_type_error:
            return transfer_type_error

        payload = {
            "ctid": str(ctid).strip(),
            "qty": str(qty).strip(),
            "symbol": str(symbol).strip() if symbol is not None else "",
            "transfer_type": transfer_type,
        }
        return self._request("POST", "/fund/transfer", json=payload)

    def fetch_user_details(
        self,
        ctid: Any,
        symbol: Any = None,
        page: int = 1,
        page_size: int = 10,
    ) -> UserDetailsResponse:
        """Fetch wallet balances and user details.

        Args:
            ctid:      Client trading ID.
            symbol:    Trading pair symbol (optional filter).
            page:      Page number for pagination.
            page_size: Records per page.

        Returns:
            :class:`~models.order_model.UserDetailsResponse` Pydantic object.
        """
        ctid_error = self._validate_ctid(ctid)
        if ctid_error:
            return UserDetailsResponse(**ctid_error)

        params: dict[str, Any] = {
            "ctid": str(ctid).strip(),
            "page": page,
            "page_size": page_size,
        }
        if symbol is not None:
            params["symbol"] = str(symbol).strip()

        raw = self._request("GET", "/user-details", params=params)
        return UserDetailsResponse.model_validate(raw)

    def wait_for_balance_update(
        self,
        ctid: Any,
        symbol: Any,
        expected_futures_value: float,
        expected_spot_value: float,
        timeout_seconds: float = 30.0,
        poll_interval: float = 2.0,
    ) -> bool:
        """Poll ``user-details`` until balances match expected values or timeout.

        Args:
            ctid:                   Client trading ID.
            symbol:                 Trading pair / symbol.
            expected_futures_value: Expected futures wallet amount.
            expected_spot_value:    Expected spot wallet amount.
            timeout_seconds:        Maximum seconds to wait (default 30).
            poll_interval:          Seconds between polls (default 2).

        Returns:
            ``True`` if both balances match within *timeout_seconds*,
            ``False`` otherwise.
        """
        tolerance = 0.01  # Allow ±0.01 for floating-point rounding
        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            details = self.fetch_user_details(ctid=ctid, symbol=symbol)
            try:
                futures_val = float(
                    details.Data.wallet_balance.futures_wallet.value or 0
                )
                spot_val = float(
                    details.Data.wallet_balance.spot_wallet.value or 0
                )
            except (TypeError, ValueError):
                time.sleep(poll_interval)
                continue

            if (
                abs(futures_val - expected_futures_value) < tolerance
                and abs(spot_val - expected_spot_value) < tolerance
            ):
                return True

            time.sleep(poll_interval)

        return False

    # -----------------------------------------------------------------------
    # Transfer-type validator (private helper)
    # -----------------------------------------------------------------------

    @staticmethod
    def _validate_transfer_type(transfer_type: Any) -> dict[str, Any] | None:
        """Ensure transfer_type is 0 (spot→futures) or 1 (futures→spot)."""
        try:
            tt = int(transfer_type)
        except (TypeError, ValueError):
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "transfer_type must be an integer (0 or 1).",
                "Data": [],
            }
        if tt not in (0, 1):
            return {
                "Status": "Failure",
                "Code": 400,
                "Message": "transfer_type must be 0 (spot→futures) or 1 (futures→spot).",
                "Data": [],
            }
        return None

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
