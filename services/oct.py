import polars as pl


class Oct:
    def __init__(self, strikes=None):
        self.strikes_count = 4
        self.strikes = strikes

    def find_valley(self, xs):
        min_ask_strikes = xs.select(
            pl.col("STRIKE"),
            pl.col("PAIR_ASK"),
        ).sort(
            pl.col("PAIR_ASK")
        )["STRIKE"].head(self.strikes_count)
        print(f"\nask valley strikes: {min_ask_strikes}")

        min_bid_strikes = xs.select(
            pl.col("STRIKE"),
            pl.col("PAIR_BID"),
        ).sort(
            pl.col("PAIR_BID")
        )["STRIKE"].head(self.strikes_count)
        print(f"\nbid valley strikes: {min_bid_strikes}")

        if any([s not in min_bid_strikes for s in min_ask_strikes]):
            print("caution: different valley for bid & ask quotes")

        return min_ask_strikes


if __name__ == '__main__':
    svc = Oct()
