from datetime import datetime
import pprint

import numpy as np
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
        self.entry_summary = []
        self.exit_summary = []

        self.pp = pprint.PrettyPrinter(indent=2)

    def calculate_safety(self, chain: pl.DataFrame):
        pass

    def enter(self, xs: pl.DataFrame):
        print(f'\n\n{"-"*10} ENTERING MARKET {"-"*10}')
        strikes_and_cashflow = self.calculate_strikes_and_cash_flow_to_enter(xs)
        net_cf = sum([x[1] for x in strikes_and_cashflow])
        if net_cf > 0.01:
            print("\nVerticalCreditSpread: opening positions for income")
            self.open = True
            print(f'cash flow: {net_cf:.2f}')
            return net_cf
        else:
            print("VerticalCreditSpread: income opportunity not available at default values of delta")
            return 0.

    def calculate_strikes_and_cash_flow_to_enter(self, xs: pl.DataFrame, short_delta=0.2, long_delta=0.1):
        print(f'{"-"*10} CALCULATING STRIKES AND CASH FLOW {"-"*10}')
        u = xs.select(
            pl.col("UNDERLYING_LAST")
        )[0,0]
        print("underlying is at: ", u)

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

        self.entry_summary = out = [
            (long_leg_down, cf_lld),
            (short_leg_down, cf_sld),
            (short_leg_up, cf_slu),
            (long_leg_up, cf_llu),
        ]
        print("strikes & cash flow on entry:")
        self.pp.pprint(out)
        return out

    def close_positions(self, xs: pl.DataFrame):
        print(f'\n\n{"-"*10} CLOSING POSITIONS {"-"*10}')
        if not self.open:
            print("VerticalCreditSpread: no open positions for today's expiry date")
            return 0.
        else:
            strikes_and_cashflow = self.calculate_strikes_and_cash_flow_to_close_positions(xs)
            net_cf = sum([x[1] for x in strikes_and_cashflow])
            print(f"{net_cf=}")
            return net_cf

    def calculate_strikes_and_cash_flow_to_close_positions(self, xs: pl.DataFrame):
        print(f'{"-"*10} CALCULATING STRIKES AND CASH FLOW {"-"*10}')

        print(f'{vcs.expiry_date=}')

        u = xs.select(
            pl.col("UNDERLYING_LAST")
        )[0,0]
        print("underlying is at: ", u)

        print("open positions with today's expiry")
        print("entry strikes and cash flows for VCS with today's expiry were: ")
        self.pp.pprint(self.entry_summary)

        # sell long positions
        cf_lld = xs.filter(
            pl.col("STRIKE") == self.long_leg_down
        )[0, "P_BID"]
        cf_llu = xs.filter(
            pl.col("STRIKE") == self.long_leg_up
        )[0, "C_BID"]

        # buy short positions
        cf_sld = -xs.filter(
            pl.col("STRIKE") == self.short_leg_down
        )[0, "P_ASK"]
        cf_slu = -xs.filter(
            pl.col("STRIKE") == self.short_leg_up
        )[0, "C_ASK"]

        self.exit_summary = out = [
            (self.long_leg_down, cf_lld),
            (self.short_leg_down, cf_sld),
            (self.short_leg_up, cf_slu),
            (self.long_leg_up, cf_llu),
        ]

        self.short_leg_down = None
        self.long_leg_down = None
        self.short_leg_up = None
        self.long_leg_up = None
        self.open = False

        print(f"strikes & cash flow to close positions:")
        self.pp.pprint(self.exit_summary)
        return out


if __name__ == "__main__":
    al = Allocator()
    al.ingest_chain("SPY", intent=Intent.INCOME)
    df = al.option_chain

    income_spreads = {}
    quote_times = df.select(
        pl.col("QUOTE_READTIME")
    ).unique().sort("QUOTE_READTIME")
    print(quote_times)

    # for qt in quote_times.to_numpy()[:10]:
    for qt in quote_times.to_numpy():
        print(f'\n\n\n{"*"*20} QUOTE READTIME: {qt} {"*"*20}')
        qd = qt[0].astype(datetime).date()
        print(f'quote date: {qd}')
        print('income spreads: ')
        pprint.pprint(list(income_spreads.keys()))

        available_expiry_dates = al.find_available_expiry_dates(qt)

        chosen_expiry_date = available_expiry_dates[0]
        print(f'\nchosen expiry date: {chosen_expiry_date}')

        xs = al.find_external_state(qt, chosen_expiry_date)

        # generate income if not already done for this expiry date
        if chosen_expiry_date not in [t[1] for t in income_spreads.keys()]:
            vcs = VerticalCreditSpread("SPY", chosen_expiry_date)
            cf_entry = vcs.enter(xs)
            income_spreads[("SPY", chosen_expiry_date)] = {
                "chosen_inflow": "oct",
                "contract": vcs,
                "cash_flows": [cf_entry],
            }
        else:
            print(f'income spread for chosen expiry date: {chosen_expiry_date} was already executed previously')

        # close positions on expiry
        for k in income_spreads.keys():
            if qd == k[1]:
                spread = income_spreads[k]
                vcs = spread["contract"]
                cf_close = vcs.close_positions(xs)
                spread["cash_flows"].append(cf_close)

    # summarize cash flows
    cfs = pl.DataFrame({"expiry_date": [''], "cash_flows": [[0., 0.]]})
    for k, v in income_spreads.items():
        cfs.extend(pl.DataFrame({
            "expiry_date": [k[1].strftime("%Y-%m-%d")],
            "cash_flows": [v["cash_flows"]],
        }))
    cfs.rechunk()

    cfs = cfs.with_columns(
        total_cf=pl.col("cash_flows").list.sum(),
    )

    print("\n\n\n")
    print(f'{"=" * 10} =========================================== {"=" * 10}')
    print(f'{"=" * 10} CASH FLOWS FROM ALL VERTICAL CREDIT SPREADS {"=" * 10}')
    print(f'{"=" * 10} =========================================== {"=" * 10}')
    pprint.pprint(cfs)
    print(f"total cash flow:{cfs['total_cf'].sum()}")
    print(f'{"=" * 10} =========================================== {"=" * 10}')
