"""
Pydantic models for the Futures API responses.

These models cover:
  - OrderResponse        : generic API envelope (Status / Code / Msg / Data)
  - WalletEntry          : a single wallet line (asset + value)
  - WalletBalance        : futures_wallet + spot_wallet pair
  - WalletBalanceData    : wrapper holding the wallet_balance object
  - UserDetailsResponse  : full user-details response parsed from the API

The test suite imports `OrderResponse` from this module; the richer
wallet-related models are needed because `fetch_user_details` returns a
structured object and the tests navigate:

    user_details.Data.wallet_balance.futures_wallet.value
    user_details.Data.wallet_balance.spot_wallet.value
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Generic API envelope
# ---------------------------------------------------------------------------

class OrderResponse(BaseModel):
    """Generic envelope returned by most Futures API endpoints."""

    Status: str = Field(default="Failure")
    Code: int = Field(default=-1)
    Msg: Optional[str] = Field(default=None)
    Message: Optional[str] = Field(default=None)
    Data: Any = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, values: Any) -> Any:
        """Accept both capitalised and lowercase key variants."""
        if not isinstance(values, dict):
            return values
        # Handle lowercase aliases sometimes returned by the API
        if "status" in values and "Status" not in values:
            values["Status"] = values.pop("status")
        if "code" in values and "Code" not in values:
            values["Code"] = values.pop("code")
        if "msg" in values and "Msg" not in values:
            values["Msg"] = values.pop("msg")
        if "message" in values and "Message" not in values:
            values["Message"] = values.pop("message")
        if "data" in values and "Data" not in values:
            values["Data"] = values.pop("data")
        return values


# ---------------------------------------------------------------------------
# Wallet-specific models (used by fetch_user_details)
# ---------------------------------------------------------------------------

class WalletEntry(BaseModel):
    """A single wallet (futures or spot) returned inside user-details."""

    asset: Optional[str] = Field(default=None)
    value: Optional[str] = Field(default=None)

    model_config = {"extra": "allow"}


class WalletBalance(BaseModel):
    """Container holding both the futures and spot wallet."""

    futures_wallet: WalletEntry = Field(default_factory=WalletEntry)
    spot_wallet: WalletEntry = Field(default_factory=WalletEntry)

    model_config = {"extra": "allow"}


class WalletBalanceData(BaseModel):
    """The `Data` portion of a user-details response."""

    wallet_balance: WalletBalance = Field(default_factory=WalletBalance)

    model_config = {"extra": "allow"}


class UserDetailsResponse(BaseModel):
    """Full response from GET /api/v1/futures/user-details."""

    Status: str = Field(default="Failure")
    Code: int = Field(default=-1)
    Msg: Optional[str] = Field(default=None)
    Message: Optional[str] = Field(default=None)
    Data: WalletBalanceData = Field(default_factory=WalletBalanceData)

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, values: Any) -> Any:
        """Accept both capitalised and lowercase key variants."""
        if not isinstance(values, dict):
            return values
        for src, dst in [("status", "Status"), ("code", "Code"),
                         ("msg", "Msg"), ("message", "Message"), ("data", "Data")]:
            if src in values and dst not in values:
                values[dst] = values.pop(src)
        return values

    model_config = {"extra": "allow"}
