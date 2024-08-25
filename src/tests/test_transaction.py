from datetime import date
from decimal import Decimal

from tomtax.transaction import Transaction


def test_transaction_split():
    t = Transaction(
        trade_id="1",
        trade_date=date(2022, 1, 1),
        instrument_code="AAPL",
        market_code="NASDAQ",
        quantity=Decimal("10"),
        price=Decimal("100"),
        transaction_type="BUY",
        currency="USD",
        transaction_fee=Decimal("10"),
        transaction_method="MARKET",
        aud_price=Decimal("150"),
    )

    t_split = t.split(Decimal("2"))
    assert t_split.quantity == Decimal("20")
    assert t_split.price == Decimal("50")
    assert t_split.aud_price == Decimal("75")
