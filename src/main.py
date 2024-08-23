import argparse

from tomtax.exchange_rates import get_exchange_rate

parser = argparse.ArgumentParser(description="tomtax: don't use this lmao")
subparsers = parser.add_subparsers(dest="command")

exchange_rates_parser = subparsers.add_parser("ex", help="Get exchange rates")
exchange_rates_parser.add_argument(
    "-c",
    "--currency",
    type=str,
    help="The currency to get the exchange rate for",
    required=True,
)
exchange_rates_parser.add_argument(
    "-d",
    "--date",
    type=str,
    help="The date to get the exchange rate for",
    required=True,
)

args = parser.parse_args()

if args.command == "ex":
    [rate, date] = get_exchange_rate(args.currency, args.date)
    print(f"$1AUD = ${rate}{args.currency.upper()} on {date}")
else:
    parser.print_help()
