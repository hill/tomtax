from datetime import date
from decimal import Decimal

import pytest

from tomtax.capital_gains import calculate_capital_gain, generate_capital_gains_report
from tomtax.transaction import Transaction


@pytest.fixture
def sample_transactions():
    """
    1 2022-01-01 BUY  10  AAPL @ $100 = $1000 / $1500 AUD
    2 2022-06-01 BUY  5   AAPL @ $120 = $600  / $900  AUD
    3 2023-01-01 SELL 15  AAPL @ $200 = $3000 / $4500 AUD

    Capital gain for first buy: (4500 - 1500) - (10 + 15) = $2975
    Capital gain for second buy: (1500 - 900) - (5 + 5*5/15) = $1595
    Total capital gain: $2975 + $1595 = $4570
    """
    return [
        Transaction(
            trade_id="1",
            trade_date=date(2022, 1, 1),
            instrument_code="AAPL",
            market_code="NASDAQ",
            quantity=Decimal("10"),
            price=Decimal("100"),
            transaction_type="BUY",
            currency="USD",
            amount=Decimal("1000"),
            transaction_fee=Decimal("10"),
            transaction_method="MARKET",
            aud_price=Decimal("150"),
            aud_amount=Decimal("1500"),
        ),
        Transaction(
            trade_id="2",
            trade_date=date(2022, 6, 1),
            instrument_code="AAPL",
            market_code="NASDAQ",
            quantity=Decimal("5"),
            price=Decimal("120"),
            transaction_type="BUY",
            currency="USD",
            amount=Decimal("600"),
            transaction_fee=Decimal("5"),
            transaction_method="MARKET",
            aud_price=Decimal("180"),
            aud_amount=Decimal("900"),
        ),
        Transaction(
            trade_id="3",
            trade_date=date(2023, 1, 1),
            instrument_code="AAPL",
            market_code="NASDAQ",
            quantity=Decimal("15"),
            price=Decimal("200"),
            transaction_type="SELL",
            currency="USD",
            amount=Decimal("3000"),
            transaction_fee=Decimal("15"),
            transaction_method="MARKET",
            aud_price=Decimal("300"),
            aud_amount=Decimal("4500"),
        ),
    ]


def test_calculate_capital_gain(sample_transactions):
    buy = sample_transactions[0]
    sell = sample_transactions[2]
    gain = calculate_capital_gain(buy, sell)
    expected_gain = Decimal("2975")  # (4500 - 1500) - (10 + 15)
    assert gain == expected_gain, f"Expected gain of {expected_gain}, but got {gain}"


def test_generate_capital_gains_report(sample_transactions):
    report = generate_capital_gains_report(sample_transactions)

    assert len(report) == 2, f"Expected 2 report entries, but got {len(report)}"

    # First entry should be for the full sale of the first buy
    assert report[0][0] == "AAPL"
    assert report[0][1] == date(2022, 1, 1)
    assert report[0][2] == date(2023, 1, 1)
    assert report[0][3] == Decimal("10")
    assert report[0][4] == Decimal("2975")
    assert report[0][5] is False
    assert report[0][6] == Decimal("100")

    # Second entry should be for the partial sale of the second buy
    assert report[1][0] == "AAPL"
    assert report[1][1] == date(2022, 6, 1)
    assert report[1][2] == date(2023, 1, 1)
    assert report[1][3] == Decimal("5")
    assert report[1][4] == Decimal("1595")  # (1500 - 900) - (5 + 5*5/15)
    assert report[1][5] is True
    assert pytest.approx(report[1][6]) == Decimal("100")


def test_fifo_order(sample_transactions):
    # Add another buy transaction with an earlier date
    early_buy = Transaction(
        trade_id="4",
        trade_date=date(2021, 12, 1),
        instrument_code="AAPL",
        market_code="NASDAQ",
        quantity=Decimal("5"),
        price=Decimal("90"),
        transaction_type="BUY",
        currency="USD",
        amount=Decimal("450"),
        transaction_fee=Decimal("5"),
        transaction_method="MARKET",
        aud_price=Decimal("135"),
        aud_amount=Decimal("675"),
    )
    transactions = [early_buy] + sample_transactions

    report = generate_capital_gains_report(transactions)

    assert len(report) == 3, f"Expected 3 report entries, but got {len(report)}"
    assert report[0][1] == date(
        2021, 12, 1
    ), "First buy should be the earliest transaction"


if __name__ == "__main__":
    pytest.main()
