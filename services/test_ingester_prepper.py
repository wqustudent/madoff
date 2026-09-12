import polars as pl

from ingester_prepper import IngesterPrepper


def test_load_option_chain():
    svc = IngesterPrepper()
    _, df = svc.load_option_chain()
    assert df.height > 0  # ensure there is data


def test_process_option_chain():
    svc = IngesterPrepper()
    _, _ = svc.load_option_chain()
    df = svc.process_option_chain()

    # ensure column names ok
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
        assert col in df.columns

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

