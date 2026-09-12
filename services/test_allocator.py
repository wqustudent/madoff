import polars as pl

from allocator import Allocator


def test_ingest_chain():
    svc = Allocator()
    for instrument in ["SPY", "SNDK"]:
        svc.ingest_chain(instrument)

        assert svc.instrument

        cols = [
            'QUOTE_READTIME',
            'QUOTE_DATE',
            'UNDERLYING_LAST',
            'EXPIRE_DATE',
            'DTE',
            'C_BID',
            'C_ASK',
            'STRIKE',
            'P_BID',
            'P_ASK',
        ]
        for col in cols:
            assert col in svc.option_chain.columns

        # ensure data types are ok
        assert svc.option_chain['QUOTE_READTIME'].dtype == pl.Datetime
        for col in ['QUOTE_DATE', 'EXPIRE_DATE']:
            assert svc.option_chain[col].dtype == pl.Date
        assert svc.option_chain['DTE'].dtype == pl.Int64
        for col in [
            'UNDERLYING_LAST',
            'C_BID',
            'C_ASK',
            'STRIKE',
            'P_BID',
            'P_ASK',
        ]:
            assert svc.option_chain[col].dtype == pl.Float64

        # ensure no null values
        assert svc.option_chain.null_count()[0].sum_horizontal().item() == 0


def test_find_available_expiry_dates():
    svc = Allocator()
    for instrument in ["SPY", "SNDK"]:
        svc.ingest_chain(instrument)

        qt = svc.option_chain.select(
            pl.col("QUOTE_READTIME")
        ).unique().sort("QUOTE_READTIME")[0].item()

        available_expiry_dates = svc.find_available_expiry_dates(qt)

        assert type(available_expiry_dates) == pl.Series
        assert len(available_expiry_dates) >= 1
        assert available_expiry_dates.is_sorted(descending=False)


def test_find_external_state():
    svc = Allocator()
    for instrument in ["SPY", "SNDK"]:
        svc.ingest_chain("SPY")

        qt = svc.option_chain.select(
            pl.col("QUOTE_READTIME")
        ).unique().sort("QUOTE_READTIME")[0].item()

        available_expiry_dates = svc.find_available_expiry_dates(qt)
        ed = available_expiry_dates[-1]

        xs = svc.find_external_state(qt, ed)

        assert type(xs) == pl.DataFrame
        assert len(xs) >= 1

        cols = [
            'QUOTE_READTIME',
            'QUOTE_DATE',
            'UNDERLYING_LAST',
            'EXPIRE_DATE',
            'DTE',
            'C_BID',
            'C_ASK',
            'STRIKE',
            'P_BID',
            'P_ASK',
            'PAIR_BID',
            'PAIR_ASK',
        ]
        for col in cols:
            assert col in xs.columns

        assert xs['QUOTE_READTIME'].dtype == pl.Datetime
        for col in ['QUOTE_DATE', 'EXPIRE_DATE']:
            assert xs[col].dtype == pl.Date
        assert xs['DTE'].dtype == pl.Int64
        for col in [
            'UNDERLYING_LAST',
            'C_BID',
            'C_ASK',
            'STRIKE',
            'P_BID',
            'P_ASK',
            'PAIR_BID',
            'PAIR_ASK',
        ]:
            assert xs[col].dtype == pl.Float64

        # ensure no null values
        assert xs.null_count()[0].sum_horizontal().item() == 0

