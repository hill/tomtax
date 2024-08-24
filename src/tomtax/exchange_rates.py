from datetime import datetime
from pathlib import Path

import pandas as pd

csv_file_path = Path(__file__).parent.parent / "data" / "exchange_rates.csv"

RBA_EXCHANGE_RATES_CSV_URL = "https://www.rba.gov.au/statistics/tables/csv/f11-data.csv"


def prepare_exchange_rates_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Set the 'Title' column as the index
    df.set_index("Title", inplace=True)

    # Skip the next 9 rows
    df = df.iloc[9:]

    # Convert the index to datetime
    df.index = pd.to_datetime(df.index, format="%d-%b-%Y")

    # Convert all data to numeric, replacing any non-numeric values with NaN
    df = df.apply(pd.to_numeric, errors="coerce")

    return df


def fetch_exchange_rates() -> pd.DataFrame:
    df = pd.read_csv(RBA_EXCHANGE_RATES_CSV_URL, skiprows=1)
    return prepare_exchange_rates_dataframe(df)


def load_and_prepare_exchange_rates(csv_file_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_file_path, skiprows=1)
    return prepare_exchange_rates_dataframe(df)


def get_exchange_rate(
    currency: str, date: str, live: bool = False
) -> tuple[float, datetime]:

    if live:
        df = fetch_exchange_rates()
    else:
        df = load_and_prepare_exchange_rates(csv_file_path)

    # Ensure the date is in datetime format
    date = pd.to_datetime(date)

    # Check if the currency exists in the DataFrame
    if f"A$1={currency.upper()}" not in df.columns:
        raise ValueError(f"Currency {currency} not found in the data")

    # Find the closest date in the index (in case the exact date is not available)
    closest_date = df.index[df.index.get_indexer([date], method="nearest")[0]]

    # Get the exchange rate
    rate = df.loc[closest_date, f"A$1={currency.upper()}"]

    return rate, closest_date


load_and_prepare_exchange_rates(csv_file_path)
