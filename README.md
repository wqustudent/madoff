# madoff

## Steps to reproduce the results
- Source data is not uploaded to this repo because Github does not allow upload of files > 100MB in size. So, you would need to download data from sources defined in data/option-chain/url.txt
  - ensure below file names after download
    - SNDK__exp_20261218.csv
    - spy_2020_2022.csv
  - refer to the following notebooks to ensure names match, data can be read, and the EDA runs ok: 
    - [load_and_EDA_for_SNDK.ipynb](notebooks/load_and_EDA_for_SNDK.ipynb)
    - [load_and_EDA_for_SPY.ipynb](notebooks/load_and_EDA_for_SPY.ipynb)
- create a virtual environment and then `pip install -r requirements.txt`
- run 
  - the allocator with `python services/allocator.py`, or
  - a jupyter notebook for backtests, i.e. notebooks/backtest_*.ipynb
