from collections import defaultdict
from decimal import Decimal

from rich import print

from tomtax.transaction import Transaction


def calculate_capital_gain(
    buy_transaction: Transaction, sell_transaction: Transaction
) -> Decimal:
    # Calculate capital gain in AUD
    capital_gain = sell_transaction.aud_amount - buy_transaction.aud_amount

    # Subtract transaction fees
    capital_gain -= buy_transaction.transaction_fee + sell_transaction.transaction_fee

    return capital_gain


def generate_capital_gains_report(transactions: list[Transaction]) -> list[tuple]:
    verbose = True

    def verbose_log(msg):
        if verbose:
            print("debug:", msg)

    buy_transactions = defaultdict(list)
    sell_transactions = defaultdict(list)
    capital_gains = []

    # Sort all transactions by date
    transactions.sort(key=lambda x: x.trade_date)

    for transaction in transactions:
        if transaction.transaction_type == "BUY":
            buy_transactions[transaction.instrument_code].append(transaction)
        elif transaction.transaction_type == "SELL":
            sell_transactions[transaction.instrument_code].append(transaction)

    # Sort buy transactions for each instrument by date to ensure FIFO
    for instrument in buy_transactions:
        buy_transactions[instrument].sort(key=lambda x: x.trade_date)

    for instrument, sells in sell_transactions.items():
        for sell in sells:
            verbose_log(f"[red]Processing sell transaction:[/] {sell}")
            remaining_quantity = sell.quantity
            while remaining_quantity > Decimal("0") and buy_transactions[instrument]:
                buy = buy_transactions[instrument][0]
                if buy.quantity <= remaining_quantity:
                    # Use entire buy transaction
                    capital_gain = calculate_capital_gain(
                        buy, sell.partial(buy.quantity)
                    )
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
                        f"[green]Consuming entire buy transaction:[/] {buy}. Capital Gain ${capital_gain:.2f}. Remaining quantity: {remaining_quantity:.2f}"
                    )
                    buy_transactions[instrument].pop(0)
                else:
                    # Use partial buy transaction
                    partial_buy = buy.partial(remaining_quantity)
                    partial_sell = sell.partial(remaining_quantity)
                    capital_gain = calculate_capital_gain(partial_buy, partial_sell)
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
                        f"[green]Using partial buy transaction:[/] {partial_buy}. Capital gain ${capital_gain:.2f}. Remaining quantity: 0. Percentage used: {percentage_used:.2f}%"
                    )
                    remaining_quantity = Decimal("0")

    return capital_gains
