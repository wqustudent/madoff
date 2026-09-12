from pathlib import Path

import pandas as pd
import polars as pl


class IngesterPrepper:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.option_chain = None

    def load_option_chain(self, instrument: str):
        if instrument == "SPY":
            return self.load_SPY_option_chain()
        elif instrument == "SNDK":
            return self.load_marketdata_app_downloaded__option_chain("SNDK")
        else:
            return None, None

    def load_marketdata_app_downloaded__option_chain(self, instrument: str):
        data_path = {
            "SNDK": self.data_dir / "option-chain" / "SNDK__exp_20261218.csv"
        }
        if instrument not in data_path.keys():
            print(f"data not found for {instrument=}")
            return None, None

        df = pl.read_csv(
            data_path[instrument],
        )
        self.option_chain = df
        return instrument, df

    def load_SPY_option_chain(self):
        instrument = "SPY"
        df = pl.read_csv(
            self.data_dir / "option-chain" / "spy_2020_2022.csv",
            # try_parse_dates=True,
        )
        # print(df)
        self.option_chain = df
        return instrument, df

    def process_option_chain(self, instrument: str):
        if instrument == "SPY":
            return self.process_SPY_option_chain()
        elif instrument == "SNDK":
            return self.process_marketdata_app_downloaded__option_chain()
        else:
            return None

    def process_marketdata_app_downloaded__option_chain(self):
        df = self.option_chain.clone()
        df = (
            df.select(
                pl.col("expiration").str.to_datetime(time_zone="UTC").dt.date(),
                pl.col("strike"),
                pl.col("dte"),
                pl.col("updated").str.to_datetime(time_zone="UTC"),
                pl.col("underlyingPrice"),
                pl.col("bid"),
                pl.col("ask"),
                pl.col("side")
            ).rename({
                "expiration": "EXPIRE_DATE",
                "strike": "STRIKE",
                "dte": "DTE",
                "updated": "QUOTE_READTIME",
                "underlyingPrice": "UNDERLYING_LAST",
                "bid": "BID",
                "ask": "ASK",
            }).with_columns(
                QUOTE_DATE=pl.col("QUOTE_READTIME").dt.date(),
                STRIKE=pl.col("STRIKE").cast(pl.Float64),
            ).pivot(
                on="side",
                index=[
                    "QUOTE_DATE",
                    "QUOTE_READTIME",
                    "EXPIRE_DATE",
                    "DTE",
                    "STRIKE",
                    "UNDERLYING_LAST",
                ],
                values=[
                    "BID",
                    "ASK",
                ]
            ).rename({
                "BID_call": "C_BID",
                "ASK_call": "C_ASK",
                "BID_put": "P_BID",
                "ASK_put": "P_ASK",
            })
        )
        print(df)
        print(df.columns)
        print(df.null_count())
        print(df.describe())
        print(type(df.null_count()))
        return df

    def process_SPY_option_chain(self):
        df = self.option_chain.clone()
        df = (
            df
            .rename(lambda c: c.strip().replace('[', '').replace(']', ''))
            .select(
                pl.col('QUOTE_READTIME'),
                pl.col('QUOTE_DATE'),
                pl.col('UNDERLYING_LAST'),
                pl.col('EXPIRE_DATE'),
                pl.col('DTE'),
                pl.col('C_BID'),
                pl.col('C_ASK'),
                pl.col('STRIKE'),
                pl.col('P_BID'),
                pl.col('P_ASK'),
            )
            .with_columns(
                pl.col('QUOTE_READTIME').str.to_datetime(" %Y-%m-%d %H:%M", strict=False),
                pl.col('QUOTE_DATE').str.to_date(" %Y-%m-%d", strict=False),
                pl.col('EXPIRE_DATE').str.to_date(" %Y-%m-%d", strict=False),

                pl.col('UNDERLYING_LAST').str.replace_all(r"[\s]", "").cast(pl.Float64, strict=False),

                pl.col('DTE').str.replace_all(r"[\s]", "").cast(pl.Float64, strict=False).cast(pl.Int64, strict=False),

                pl.col('C_BID').str.replace_all(r"[\s]", "").cast(pl.Float64, strict=False),
                pl.col('C_ASK').str.replace_all(r"[\s]", "").cast(pl.Float64, strict=False),
                pl.col('STRIKE').str.replace_all(r"[\s]", "").cast(pl.Float64, strict=False),
                pl.col('P_BID').str.replace_all(r"[\s]", "").cast(pl.Float64, strict=False),
                pl.col('P_ASK').str.replace_all(r"[\s]", "").cast(pl.Float64, strict=False),
            ).drop_nulls()
        )
        # print(df)
        # print(df.null_count())
        # print(df.describe())
        # print(type(df.null_count()))
        self.option_chain = df
        return df


if __name__ == "__main__":
    svc = IngesterPrepper()
    # _ = svc.load_SPY_option_chain()
    # df = svc.process_SPY_option_chain()
    svc.load_option_chain("SNDK")
    svc.process_option_chain("SNDK")
