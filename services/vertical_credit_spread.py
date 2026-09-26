import pprint

import polars as pl

from allocator import Allocator, Intent


class VerticalCreditSpread:
    def __init__(self, underlying: str, expiry_date):
        self.underlying = underlying
        self.expiry_date = expiry_date
        self.safety = None

        self.short_leg_up = None
        self.long_leg_up = None
        self.short_leg_down = None
        self.long_leg_down = None

        self.open = False

        self.pp = pprint.PrettyPrinter(indent=2)

    def calculate_safety(self, chain: pl.DataFrame):
        pass

    def enter(self, xs: pl.DataFrame):
        strikes_and_cashflow = self.calculate_strikes_and_cash_flow(xs)
        net_cf = sum([x[1] for x in strikes_and_cashflow])
        if net_cf > 0:
            print("VerticalCreditSpread: opening positions for income")
            self.open = True
            return net_cf
        else:
            print("VerticalCreditSpread: income opportunity not available at default values of delta")
            return 0

    def calculate_strikes_and_cash_flow(self, xs: pl.DataFrame, short_delta=0.2, long_delta=0.1):
        print(f'\n\n{"*"*10} CALCULATING STRIKES AND CASH FLOW {"*"*10}')
        u = xs.select(
            pl.col("UNDERLYING_LAST")
        )[0,0]
        print("underlying at: ", u)

        # ################################ #
        # calculate strikes for the spread #
        # ################################ #
        short_leg_up = xs.filter(
            pl.col("C_DELTA") < short_delta
        ).sort("C_DELTA", descending=True)[0, "STRIKE"]
        # print("\nshort leg up:", short_leg_up)
        self.short_leg_up = short_leg_up

        long_leg_up = xs.filter(
            pl.col("C_DELTA") < long_delta
        ).sort("C_DELTA", descending=True)[0, "STRIKE"]
        # print("long leg up:", long_leg_up)
        self.long_leg_up = long_leg_up

        short_leg_down = xs.filter(
            pl.col("P_DELTA") > -short_delta
        ).sort("P_DELTA", descending=False)[0, "STRIKE"]
        # print("\nshort leg down:", short_leg_down)
        self.short_leg_down = short_leg_down

        long_leg_down = xs.filter(
            pl.col("P_DELTA") > -long_delta
        ).sort("P_DELTA", descending=False)[0, "STRIKE"]
        # print("long leg down:", long_leg_down)
        self.long_leg_down = long_leg_down

        # ################################ #
        # calculate cash flows from spread #
        # ################################ #
        cf_slu = xs.filter(
            pl.col('STRIKE') == short_leg_up
        )[0, "C_BID"]
        # print("\ncash flow::short leg up:", cf_slu)

        cf_llu = -xs.filter(
            pl.col('STRIKE') == long_leg_up
        )[0, "C_ASK"]
        # print("cash flow::long leg up:", cf_llu)

        cf_sld = xs.filter(
            pl.col('STRIKE') == short_leg_down
        )[0, "P_BID"]
        # print("cash flow::short leg down:", cf_sld)

        cf_lld = -xs.filter(
            pl.col('STRIKE') == long_leg_down
        )[0, "P_ASK"]
        # print("cash flow::long leg down:", cf_lld)

        out = [
            (long_leg_down, cf_lld),
            (short_leg_down, cf_sld),
            (short_leg_up, cf_slu),
            (long_leg_up, cf_llu),
        ]
        print("strikes & cash flow:")
        self.pp.pprint(out)
        return out


if __name__ == "__main__":
    al = Allocator()
    al.ingest_chain("SPY", intent=Intent.INCOME)
    df = al.option_chain

    qt = df.select(
        pl.col("QUOTE_READTIME")
    ).unique().sort("QUOTE_READTIME")[0].item()
    print("\nquote time", qt)

    available_expiry_dates = al.find_available_expiry_dates(qt)

    chosen_expiry_date = available_expiry_dates[1]
    print(f'\nchosen expiry date: {chosen_expiry_date}')

    xs = al.find_external_state(qt, chosen_expiry_date)

    vcs = VerticalCreditSpread("SPY", chosen_expiry_date)
    vcs.enter(xs)
