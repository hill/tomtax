from datetime import date
from decimal import Decimal

import pytest

from tomtax.capital_gains import (
    adjust_transactions_for_splits,
    calculate_capital_gain,
    generate_capital_gains_report,
)
from tomtax.transaction import StockSplit, Transaction


@pytest.fixture
def sample_transactions():
    return [
        Transaction(
            trade_id="1",
            trade_date=date(2023, 1, 1),
            instrument_code="NVDA",
            market_code="NASDAQ",
            quantity=Decimal("10"),
            price=Decimal("100"),
            transaction_type="BUY",
            currency="USD",
            aud_price=Decimal("150"),
        ),
        Transaction(
            trade_id="2",
            trade_date=date(2023, 6, 1),
            instrument_code="NVDA",
            market_code="NASDAQ",
            quantity=Decimal("5"),
            price=Decimal("200"),
            transaction_type="SELL",
            currency="USD",
            aud_price=Decimal("300"),
        ),
        Transaction(
            trade_id="3",
            trade_date=date(2023, 8, 1),
            instrument_code="NET",
            market_code="NASDAQ",
            quantity=Decimal("1"),
            price=Decimal("100"),
            transaction_type="BUY",
            currency="USD",
            aud_price=Decimal("200"),
        ),
    ]


@pytest.fixture
def sample_splits():
    return {"NVDA": [StockSplit(date=date(2023, 7, 1), ratio=Decimal("4"))]}


def test_adjust_transactions_for_splits(sample_transactions, sample_splits):
    adjusted = adjust_transactions_for_splits(sample_transactions, sample_splits)

    assert len(adjusted) == 3
    assert adjusted[0].quantity == Decimal("40")  # 10 * 4
    assert adjusted[0].price == Decimal("25")  # 100 / 4
    assert adjusted[0].aud_price == Decimal("37.5")  # 150 / 4

    assert adjusted[1].quantity == Decimal("20")  # 5 * 4
    assert adjusted[1].price == Decimal("50")  # 200 / 4
    assert adjusted[1].aud_price == Decimal("75")  # 300 / 4

    assert adjusted[2].quantity == Decimal("1")
    assert adjusted[2].price == Decimal("100")
    assert adjusted[2].aud_price == Decimal("200")


def test_calculate_capital_gain():
    buy = Transaction(
        trade_id="1",
        trade_date=date(2023, 1, 1),
        instrument_code="AAPL",
        market_code="NASDAQ",
        quantity=Decimal("10"),
        price=Decimal("100"),
        transaction_type="BUY",
        currency="USD",
        aud_price=Decimal("150"),
    )
    sell = Transaction(
        trade_id="2",
        trade_date=date(2023, 6, 1),
        instrument_code="AAPL",
        market_code="NASDAQ",
        quantity=Decimal("10"),
        price=Decimal("200"),
        transaction_type="SELL",
        currency="USD",
        aud_price=Decimal("300"),
    )

    gain = calculate_capital_gain(buy, sell, Decimal("5"))
    assert gain == Decimal("750")  # (300 - 150) * 5


def test_generate_capital_gains_report(sample_transactions):
    report = generate_capital_gains_report(sample_transactions, {})

    assert len(report) == 1
    assert report[0][0] == "NVDA"
    assert report[0][1] == date(2023, 1, 1)
    assert report[0][2] == date(2023, 6, 1)
    assert report[0][3] == Decimal("5")
    assert report[0][4] == Decimal("750")  # (300 - 150) * 5
    assert report[0][5] is True  # Partial buy
    assert report[0][6] == Decimal("50")
