import click

from tomtax.exchange_rates import get_exchange_rate


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


cli.add_command(ex)
cli.add_command(tx)

if __name__ == "__main__":
    cli()
