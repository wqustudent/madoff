import pprint

import polars as pl

from ingester_prepper import IngesterPrepper
from oct import Oct


class Allocator:
    def __init__(self):
        self.ingester_prepper = IngesterPrepper()
        self.instrument = None
        self.option_chain = None

        self.ladder = {}
        self.outflow_now__inflow_later__choices = [
            "pair",  # call + put @ same strike: inflow is not guaranteed as instrument may expire at the strike price
            "quad",  # 2 pairs @ different strikes: market-maker guarantees cash inflow @settlement/expiry-date
            "hex",   # 3 pairs: allows for mechanical expansion of cash inflow guarantee @settlement as underlying moves up/down
            "oct",   # 4 pairs: allows for cash collection when moving within the extremes as well
            "dec",   # 5 pairs: may be suitable for highly volatile instruments (more cash collection during each step/move)
            "doz",   # 6 pairs: ^
        ]

        self.pp = pprint.PrettyPrinter(indent=2)

    def run(self):
        # self.ingest_chain("SPY")
        self.ingest_chain("SNDK")
        instrument = self.instrument
        df = self.option_chain

        entry_time = df.select(
            pl.col("QUOTE_READTIME")
        ).unique().sort("QUOTE_READTIME")[0].item()

        available_expiry_dates = self.find_available_expiry_dates(entry_time)

        chosen_expiry_date = available_expiry_dates[-1]
        print(f'\nchosen expiry date: {chosen_expiry_date}')

        xs = self.find_external_state(entry_time, chosen_expiry_date)
        contract = self.allocate_oct_to_ladder(xs, entry_time, instrument, chosen_expiry_date)

        quote_times = df.filter(
            pl.col("EXPIRE_DATE") == chosen_expiry_date
        )["QUOTE_READTIME"].unique().sort()
        print(f"\nquote times for expiry {chosen_expiry_date}: {quote_times}")

        for qt in quote_times:
            try:
                xs = self.find_external_state(qt, chosen_expiry_date)
                print(f"\n\n{'*'*20} ********************************** {'*'*20}")
                print(f"{'*'*20} EVALUATING REBALANCING OPPORTUNITY {'*'*20}")
                print(f"{'*'*17} ({qt=}) {'*'*16}")
                print(f"{'*'*20} ********************************** {'*'*20}")
                cf, sg = contract.rebalance(xs)
                if cf:
                    self.ladder[(instrument, chosen_expiry_date)]["cash"].extend(pl.DataFrame({
                        "QUOTE_TIME": [qt],
                        "FLOW": [cf],
                        "SETTLEMENT_GUARANTEE": [sg],
                    }))
            except Exception as e:
                print(f"\n\n\nAN ERROR OCCURRED WHILE REBALANCING WHEN {qt=}: {e}")
            finally:
                print(f"\n\n\n\n{'*'*20} ************** {'*'*20}")
                print(f"{'*'*20} LADDER HISTORY {'*'*20}")
                print(f"{'*'*20} *** (CASH) *** {'*'*20}")
                print(self.ladder)

    def allocate_oct_to_ladder(self, xs, entry_time, instrument, chosen_expiry_date):
        print("\nallocating oct_ to ladder.")
        oct_ = Oct(chosen_expiry_date)
        cf = oct_.enter_market(xs)
        sg = oct_.settlement_guarantee
        print(f"{sg}")
        self.ladder[(instrument, chosen_expiry_date)] = {
            "chosen_inflow": "oct",
            "contract": oct_,
            "cash": pl.DataFrame({
                "QUOTE_TIME": [entry_time],
                "FLOW": [cf],
                "SETTLEMENT_GUARANTEE": [sg],
            }),
        }
        print("ladder: ")
        self.pp.pprint(self.ladder)
        return oct_

    def ingest_chain(self, instrument):
        sub = self.ingester_prepper
        _, _ = sub.load_option_chain(instrument)
        df = sub.process_option_chain(instrument)
        print("\nloaded option chain: ", df)
        self.option_chain = df
        self.instrument = instrument

    def find_available_expiry_dates(self, quote_time):
        df = self.option_chain
        available_expiry_dates = df.filter(
            pl.col("QUOTE_READTIME") == quote_time
        )["EXPIRE_DATE"].unique().sort()
        print(f"\navailable expiry dates on {quote_time=}: ", available_expiry_dates)
        return available_expiry_dates

    def find_external_state(self, quote_time, expiry_date):
        df = self.option_chain

        # find external-state or expiry-speculation
        xs = df.filter(
            (pl.col("QUOTE_READTIME") == quote_time)
            & (pl.col("EXPIRE_DATE") == expiry_date)
        ).with_columns(
            (pl.col("C_ASK") + pl.col("P_ASK")).alias("PAIR_ASK"),
            (pl.col("C_BID") + pl.col("P_BID")).alias("PAIR_BID"),
        )
        return xs


if __name__ == '__main__':
    svc = Allocator()
    svc.run()
