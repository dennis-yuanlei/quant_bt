import akshare as ak
import ipdb
import pandas

stock_id = "000852"

# 股票
# stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_id, period="daily", start_date="20210101", end_date='202301231', adjust="hfq")
# stock_zh_a_hist_df.to_csv(f'{stock_id}.csv', index=False)
# 指数
stock_zh_index_daily_df = ak.index_zh_a_hist(symbol=stock_id, period="daily",)
stock_zh_index_daily_df.to_csv(f'{stock_id}.csv', index=False)