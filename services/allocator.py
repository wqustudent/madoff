import polars as pl

from ingester_prepper import IngesterPrepper


class Allocator:
    def __init__(self):
        self.ingester_prepper = IngesterPrepper()
        self.option_chain = None

    def run(self):
        self.ingest_chain()
        df = self.option_chain

        entry_time = df.select(
            pl.col("QUOTE_READTIME")
        ).unique().sort("QUOTE_READTIME")[0].item()

        available_expiry_dates = self.find_available_expiry_dates(entry_time)
        chosen_expiry_date = available_expiry_dates[-1]
        print(f'\nchosen expiry date: {chosen_expiry_date}')

    def ingest_chain(self):
        sub = self.ingester_prepper
        sub.load_option_chain()
        df = sub.process_option_chain()
        print("\nloaded option chain: ", df)
        self.option_chain = df

    def find_available_expiry_dates(self, quote_time):
        df = self.option_chain
        available_expiry_dates = df.filter(
            pl.col("QUOTE_READTIME") == quote_time
        )["EXPIRE_DATE"].unique()
        print("\navailable expiry dates: ", available_expiry_dates)
        return available_expiry_dates


if __name__ == '__main__':
    svc = Allocator()
    svc.run()
