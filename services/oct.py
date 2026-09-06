import polars as pl


class Oct:
    def __init__(self, strikes=None):
        self.strikes_count = 4
        self.strikes = strikes

        if strikes is not None:
            s0, s1, s2, s3 = sorted(strikes)
            self.settlement_guarantee = (s3-s0) + (s2-s1)
        else:
            self.settlement_guarantee = None

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

    def enter_market(self, xs):
        print(f"\nentering the market at strikes: {self.strikes}")
        if self.strikes is None:
            print("no strikes defined")
            return None
        cf = 0
        for strike in self.strikes:
            cost = xs.filter(
                (pl.col("STRIKE") == strike)
            )["PAIR_ASK"].item()
            print(f"cost for {strike=}: {cost}")
            cf -= cost
        print(f"total cash flow: {cf}")
        return cf


if __name__ == '__main__':
    svc = Oct()
