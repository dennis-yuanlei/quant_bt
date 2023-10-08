import akshare as ak
import ipdb
import pandas

stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="601127", period="daily", start_date="20210101", end_date='202301231', adjust="hfq")
stock_zh_a_hist_df.to_csv('601127.csv', index=False)
# ipdb.set_trace()
print(stock_zh_a_hist_df)