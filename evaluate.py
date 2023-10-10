from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import ipdb
import random

# Import the backtrader platform
import backtrader as bt

import akshare as ak

def evaluate(num, start_date, end_date, id_path='./all_stock_id.txt'):
    # 随机从A股中选出cnt支股票评估
    stock_ids = open(id_path, 'r').read().strip().split(',')
    random.shuffle(stock_ids)
    cnt = 0
    i=0
    while cnt<=num:
        _id = stock_ids[i]
        if _id[:3] not in ['600', '601', '605', '000']:
            continue
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=_id, period="daily", start_date=start_date, end_date=end_date, adjust="hfq")
        data = bt.feeds.GenericCSVData(
                dataname='./002642.csv',

                fromdate=datetime.datetime(2023, 1, 1),
                todate=datetime.datetime(2023, 12, 31),
                nullvalue=0.0,
                dtformat=('%Y-%m-%d'),
                datetime=0,
                open=1,
                close=2,
                high=3,
                low=4,
                volume=5,
                openinterest=-1)
        cerebro = bt.Cerebro()
        cerebro.adddata(data, name=_id)
        
        i += 1
        

if __name__ == "__main__":
    evaluate(50, '20230101', '20231231')

