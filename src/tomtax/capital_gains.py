from collections import defaultdict
from decimal import Decimal
from typing import Dict, List

from rich import print

from tomtax.transaction import StockSplit, Transaction


def adjust_transaction_for_splits(
    transaction: Transaction, splits: Dict[str, List[StockSplit]]
) -> Transaction:

    total_ratio = Decimal("1")
    for split in splits.get(transaction.instrument_code, []):
        if split.date > transaction.trade_date:
            total_ratio *= split.ratio

    if total_ratio != Decimal("1"):
        return transaction.split(total_ratio)

    return transaction


def adjust_transactions_for_splits(
    transactions: List[Transaction], splits: Dict[str, List[StockSplit]]
) -> List[Transaction]:
    return [adjust_transaction_for_splits(t, splits) for t in transactions]


def calculate_capital_gain(
    buy_transaction: Transaction, sell_transaction: Transaction, sell_quantity: Decimal
) -> Decimal:
    # Calculate the portion of the sell transaction we're using
    sell_portion = sell_quantity / sell_transaction.quantity

    # Calculate capital gain in AUD
    buy_amount = buy_transaction.aud_amount * (sell_quantity / buy_transaction.quantity)
    sell_amount = sell_transaction.aud_amount * sell_portion

    return sell_amount - buy_amount


def generate_capital_gains_report(
    transactions: list[Transaction], splits: Dict[str, List[StockSplit]]
) -> list[tuple]:
    verbose = True

    def verbose_log(msg):
        if verbose:
            print(msg)

    adjusted_transactions = adjust_transactions_for_splits(transactions, splits)

    buy_transactions = defaultdict(list)
    sell_transactions = defaultdict(list)
    capital_gains = []

    # Sort all transactions by date
    adjusted_transactions.sort(key=lambda x: x.trade_date)

    for transaction in adjusted_transactions:
        if transaction.transaction_type == "BUY":
            buy_transactions[transaction.instrument_code].append(transaction)
        elif transaction.transaction_type == "SELL":
            sell_transactions[transaction.instrument_code].append(transaction)

    # Sort buy transactions for each instrument by date to ensure FIFO
    for instrument in buy_transactions:
        buy_transactions[instrument].sort(key=lambda x: x.trade_date)

    for instrument, sells in sell_transactions.items():
        for sell in sells:
            verbose_log(f"[red]Processing sell transaction:[/]\n\t{sell}\n")
            remaining_quantity = sell.quantity
            while remaining_quantity > Decimal("0") and buy_transactions[instrument]:
                buy = buy_transactions[instrument][0]
                if buy.quantity <= remaining_quantity:
                    # Use entire buy transaction
                    capital_gain = calculate_capital_gain(buy, sell, buy.quantity)
                    capital_gains.append(
                        (
                            instrument,
                            buy.trade_date,
                            sell.trade_date,
                            buy.quantity,
                            capital_gain,
                            False,  # Not a partial buy
                            Decimal("100"),  # 100% of the buy transaction used
                        )
                    )
                    remaining_quantity -= buy.quantity
                    verbose_log(
                        f"[green]Consuming entire buy transaction:[/]\n\t{buy}\n\tCapital Gain ${capital_gain:.2f}\n\tRemaining quantity: {remaining_quantity:.2f}\n"
                    )
                    buy_transactions[instrument].pop(0)
                else:
                    # Use partial buy transaction
                    capital_gain = calculate_capital_gain(buy, sell, remaining_quantity)
                    percentage_used = (remaining_quantity / buy.quantity) * Decimal(
                        "100"
                    )
                    capital_gains.append(
                        (
                            instrument,
                            buy.trade_date,
                            sell.trade_date,
                            remaining_quantity,
                            capital_gain,
                            True,  # This is a partial buy
                            percentage_used,
                        )
                    )
                    buy.quantity -= remaining_quantity
                    verbose_log(
                        f"[green]Using partial buy transaction:[/]\n\t{buy}\n\tCapital gain ${capital_gain:.2f}\n\tRemaining buy quantity: {buy.quantity:.2f}\n\tPercentage used: {percentage_used:.2f}%\n"
                    )
                    remaining_quantity = Decimal("0")

    return capital_gains
