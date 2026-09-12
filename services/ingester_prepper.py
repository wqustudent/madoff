from pathlib import Path

import polars as pl


class IngesterPrepper:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.option_chain = None

    def load_SPY_option_chain(self):
        instrument = "SPY"
        df = pl.read_csv(
            self.data_dir / "option-chain" / "spy_2020_2022.csv",
            # try_parse_dates=True,
        )
        # print(df)
        self.option_chain = df
        return instrument, df

    def process_option_chain(self):
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
    _ = svc.load_SPY_option_chain()
    df = svc.process_option_chain()
