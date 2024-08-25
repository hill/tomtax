import csv
from datetime import date, datetime
from decimal import Decimal

import click
from rich.console import Console
from rich.table import Table

from tomtax.capital_gains import generate_capital_gains_report
from tomtax.exchange_rates import get_exchange_rate
from tomtax.transaction import StockSplit, Transaction, render_transactions_table


@click.group()
def cli():
    """tomtax: don't use this lmao"""
    pass


@click.command()
@click.option(
    "-c",
    "--currency",
    type=str,
    help="The currency to get the exchange rate for",
    required=True,
)
@click.option(
    "-d",
    "--date",
    type=str,
    help="The date to get the exchange rate for",
    required=True,
)
@click.option(
    "--live",
    is_flag=True,
    help="Fetch the latest exchange rates from the RBA website",
    default=False,
)
def ex(currency, date, live):
    """Get exchange rates"""
    rate, date = get_exchange_rate(currency, date, live)
    print(f"$1AUD = ${rate}{currency.upper()} on {date}")


@click.group()
def tx():
    """Manage transactions"""
    pass


def read_csv(file_path: str) -> list[Transaction]:
    transactions = []
    with open(file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            full_datetime = datetime.strptime(
                row["Trade date"], "%Y-%m-%d %H:%M:%S.%f (%Z)"
            )
            transaction = Transaction(
                trade_id=row["Trade ID"],
                trade_date=full_datetime.date(),
                instrument_code=row["Instrument code"],
                market_code=row["Market code"],
                quantity=Decimal(row["Quantity"]),
                price=Decimal(row["Price"]),
                transaction_type=row["Transaction type"],
                currency=row["Currency"],
                # amount=Decimal(row["Amount"]),
                transaction_fee=Decimal(row["Transaction fee"]),
                transaction_method=row["Transaction method"],
            )
            transactions.append(transaction)
    return transactions


def convert_to_aud(transactions: list[Transaction]):
    for transaction in transactions:
        if transaction.currency.lower() == "aud":
            transaction.aud_price = transaction.price
        else:
            rate, _ = get_exchange_rate(
                transaction.currency,
                transaction.trade_date.strftime("%Y-%m-%d"),
                live=False,
            )
            transaction.aud_price = transaction.price / Decimal(str(rate))


@click.command()
@click.argument("file", type=click.Path(exists=True))
def read(file: str):
    """Read transactions from a CSV file"""
    transactions = read_csv(file)
    convert_to_aud(transactions)
    render_transactions_table(transactions)


@click.command()
@click.argument("file", type=click.Path(exists=True))
def report(file: str):
    """Generate a capital gains report for all transactions"""
    transactions = read_csv(file)
    convert_to_aud(transactions)

    stock_splits = {"NVDA": [StockSplit(date=date(2024, 6, 7), ratio=Decimal("10"))]}

    capital_gains = generate_capital_gains_report(transactions, stock_splits)

    console = Console()
    table = Table(title="Capital Gains Report")

    table.add_column("Instrument", style="cyan")
    table.add_column("Buy Date", style="green")
    table.add_column("Sell Date", style="red")
    table.add_column("Quantity", style="blue")
    table.add_column("Capital Gain/Loss", style="yellow")
    table.add_column("Partial Buy", style="magenta")

    total_capital_gain = Decimal("0")
    for (
        instrument,
        buy_date,
        sell_date,
        quantity,
        gain,
        is_partial,
        percentage_used,
    ) in capital_gains:
        partial_info = f"Yes ({percentage_used:.2f}%)" if is_partial else "No"
        table.add_row(
            instrument,
            buy_date.strftime("%Y-%m-%d"),
            sell_date.strftime("%Y-%m-%d"),
            f"{quantity:.6f}",
            f"${gain:.2f}",
            partial_info,
        )
        total_capital_gain += gain

    table.add_row("", "", "", "", "Total", f"${total_capital_gain:.2f}", style="bold")
    console.print(table)


tx.add_command(report)
tx.add_command(read)
cli.add_command(ex)
cli.add_command(tx)

if __name__ == "__main__":
    cli()
