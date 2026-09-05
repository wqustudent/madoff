from pathlib import Path

import polars as pl


class IngesterPrepper:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"

    def load_option_chain(self):
        df = pl.read_csv(
            self.data_dir / "option-chain" / "nvda_2020_2022.csv",
            # try_parse_dates=True,
        )
        print(df)
        return df


if __name__ == "__main__":
    svc = IngesterPrepper()
    _ = svc.load_option_chain()
