from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class Transaction:
    date: datetime
    txn_type: Literal["BUY"] | Literal["SELL"]
    market_code: str
    instrument_code: str
    currency: str
    quantity: float
    price_per_unit: float
    aud_price_per_unit: float = 0.0
    platform: str = "Sharesies"
    platform_fee: float = 0.0
    platform_id: str = ""
