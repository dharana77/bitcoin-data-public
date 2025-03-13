from alpha_vantage.timeseries import TimeSeries
import pandas as pd

api_key = "97THOP2A5LS7PDPK"  # 무료 API 키 필요 (https://www.alphavantage.co/support/#api-key)
ts = TimeSeries(key=api_key, output_format="pandas")
data, meta = ts.get_intraday(symbol="TSLA", interval="15min", outputsize="full")  # full: 최대 5년
data.to_csv("stock_15m.csv")