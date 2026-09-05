import polars as pl

from ingester_prepper import IngesterPrepper


def test_load_option_chain():
    svc = IngesterPrepper()
    df = svc.load_option_chain()
    assert df.height > 0  # ensure there is data


def test_process_option_chain__columns_present():
    svc = IngesterPrepper()
    _ = svc.load_option_chain()
    df = svc.process_option_chain()

    # ensure column names ok
    assert df.columns == [
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

    # ensure data types are ok
    assert df['QUOTE_READTIME'].dtype == pl.Datetime
    for col in ['QUOTE_DATE', 'EXPIRE_DATE']:
        assert df[col].dtype == pl.Date
    assert df['DTE'].dtype == pl.Int64
    for col in [
        'UNDERLYING_LAST',
        'C_BID',
        'C_ASK',
        'STRIKE',
        'P_BID',
        'P_ASK',
    ]:
        assert df[col].dtype == pl.Float64

    # ensure no null values
    assert df.null_count()[0].sum_horizontal().item() == 0

