import pprint

import polars as pl


class Oct:
    def __init__(self, strikes=None):
        self.strikes_count = 4
        self.strikes = strikes
        self.settlement_guarantee = None

        self.pp = pprint.PrettyPrinter(indent=2)

    def rebalance(self, xs):
        collection_moves = self.evaluate_if_cash_collection_possible(xs)
        if collection_moves:
            pass

    def evaluate_if_cash_collection_possible(self, xs):
        print(f"\nevaluating external state: {xs}")
        min_ask_strikes = self._find_valley(xs)
        collection_moves = []
        for to_strike in min_ask_strikes:
            print(f"\n{'-'*50}")
            print(f"assessing move {to_strike=}")

            move_direction = self._find_move_direction(to_strike=to_strike)
            print(f"{move_direction=}")

            strikes_in_play = self._strikes_in_play(move_direction)
            print(f"{strikes_in_play=}")

            for from_strike in strikes_in_play:
                # evaluate expected cash flow
                exp_cf = self._expected_cash_flow(xs, from_strike=from_strike, to_strike=to_strike)
                print(f"{exp_cf=:.2f} if moving {from_strike=} {to_strike=}")
                if exp_cf > 0:
                    # collection_moves.append((from_strike, to_strike, exp_cf))
                    collection_moves.append({
                        "from_strike": from_strike,
                        "to_strike": to_strike,
                        "exp_cf": exp_cf
                    })

            print(f"can collect cash with collection moves:")
            self.pp.pprint(collection_moves)
        return collection_moves

    def _find_move_direction(self, to_strike):
        at_strikes = sorted(self.strikes)
        s0, s1, s2, s3 = at_strikes
        if to_strike > s3:
            move_direction = "UP"
        elif to_strike < s0:
            move_direction = "DOWN"
        elif to_strike not in at_strikes:
            move_direction = "IN"
        else: # already positioned at to_strike
            move_direction = None
        if move_direction is not None:
            print(f"{to_strike=} is in the ask valley and not in current positions @{at_strikes}")
        return move_direction

    def _strikes_in_play(self, move):
        s0, s1, s2, s3 = sorted(self.strikes)
        if move == "UP":
            return [s1, s2, s3]
        elif move == "DOWN":
            return [s0, s1, s2]
        elif move == "IN":
            return [s1, s2]
        return []

    @staticmethod
    def _expected_cash_flow(xs, from_strike, to_strike):
        in_ = xs.filter(
            pl.col("STRIKE") == from_strike
        )["PAIR_BID"].item()
        out = xs.filter(
            pl.col("STRIKE") == to_strike
        )["PAIR_ASK"].item()
        return in_ - out

    def _find_valley(self, xs):
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
        min_ask_strikes = self._find_valley(xs)
        print(f"\nentering the market at strikes: {self.strikes}")
        self.strikes = min_ask_strikes
        s0, s1, s2, s3 = sorted(min_ask_strikes)
        self.settlement_guarantee = (s3 - s0) + (s2 - s1)
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
