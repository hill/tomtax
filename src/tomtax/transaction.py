from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from rich.console import Console
from rich.table import Table


@dataclass
class Transaction:
    trade_id: str
    trade_date: date
    instrument_code: str
    market_code: str
    quantity: Decimal
    price: Decimal
    transaction_type: Literal["BUY", "SELL"]
    currency: str
    transaction_fee: Decimal
    transaction_method: str
    aud_price: Decimal = Decimal("0")

    def __post_init__(self):
        if self.transaction_type not in ["BUY", "SELL"]:
            raise ValueError("Transaction type must be either 'BUY' or 'SELL'")

    def __str__(self):
        return f"TX<{self.trade_date} {self.instrument_code} {self.transaction_type} {self.quantity} @ ${self.price}{self.currency} = ${self.amount} [${self.aud_price:.2f}aud = ${self.aud_amount:.2f}]>"

    @property
    def amount(self) -> Decimal:
        return self.quantity * self.price

    @property
    def aud_amount(self) -> Decimal:
        return self.quantity * self.aud_price

    def partial(self, new_quantity: Decimal) -> "Transaction":
        """Create a partial transaction with the given quantity."""
        fraction = new_quantity / self.quantity
        return Transaction(
            trade_id=self.trade_id,
            trade_date=self.trade_date,
            instrument_code=self.instrument_code,
            market_code=self.market_code,
            quantity=new_quantity,
            price=self.price,
            transaction_type=self.transaction_type,
            currency=self.currency,
            transaction_fee=self.transaction_fee * fraction,
            transaction_method=self.transaction_method,
            aud_price=self.aud_price,
        )


def render_transactions_table(transactions: list[Transaction]):
    console = Console()
    table = Table(title="Transactions")

    table.add_column("Trade Date", style="cyan")
    table.add_column("Instrument", justify="center", style="magenta")
    table.add_column("Type", justify="center")
    table.add_column("Quantity", style="yellow")
    table.add_column("Price", style="blue")
    table.add_column("Amount", style="red")
    table.add_column("AUD Amount", style="red")

    for t in transactions:
        table.add_row(
            t.trade_date.strftime("%Y-%m-%d"),
            t.instrument_code,
            "[on green]BUY[/]" if t.transaction_type == "BUY" else "[on red]SELL[/]",
            f"{t.quantity:.2f}",
            f"{t.price:.2f} {t.currency.upper()}",
            f"{t.amount:.2f} {t.currency.upper()}",
            f"{t.aud_amount:.2f} AUD",
        )

    console.print(table)
