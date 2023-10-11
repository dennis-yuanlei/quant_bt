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

class ACommission(bt.CommInfoBase):
    params = (
        ('stocklike', True), # 指定为股票模式
        ('commtype', bt.CommInfoBase.COMM_PERC), # commission使用百分比费用模式
        ('percabs', False), # commission理解为百分数
        ('stamp_duty', 0.0005), # 印花税默认为 0.05%
        ('commission', 0.01))  #佣金万1
    
        # 自定义费用计算公式
    def _getcommission(self, size, price, pseudoexec):
            if size > 0: # 买入时，考虑佣金(万一不免5)
                return max(abs(size) * price * self.p.commission, 5)
            elif size < 0: # 卖出时，同时考虑佣金和印花税过户费
                return max(abs(size) * price * self.p.commission, 5) + abs(size) * price *  self.p.stamp_duty
            else:
                return 0

def evaluate(num, start_date, end_date, mystrategy=None, mysignal=None, id_path='./all_stock_id.txt'):
    # 随机从A股中选出num支股票评估
    os.makedirs('./datas', exist_ok=True)
    stock_ids = open(id_path, 'r').read().strip().split(',')
    random.shuffle(stock_ids)
    avg_AnnualReturn = 0
    avg_DrawDown = 0
    avg_SharpeRatio = 0
    cnt = 0
    i=0
    while cnt<=num:
        _id = stock_ids[i]
        if _id[:2] not in ['60', '00']:
            i += 1
            continue
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=_id, period="daily", start_date=start_date, end_date=end_date, adjust="hfq")
        if len(stock_zh_a_hist_df)<100:
            i += 1
            continue
        print(f'evaluate@{_id}')
        stock_zh_a_hist_df.to_csv(f'./datas/{_id}.csv', index=False)
        print('downloading data over')
        data = bt.feeds.GenericCSVData(
                dataname=f'./datas/{_id}.csv',
                fromdate=datetime.datetime(int(start_date[:4]), int(start_date[4:6]), int(start_date[6:8])),
                todate=datetime.datetime(int(end_date[:4]), int(end_date[4:6]), int(end_date[6:8])),
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

        if mysignal:
            cerebro.add_signal(bt.SIGNAL_LONG, mysignal)
            cerebro.signal_accumulate(True)
            cerebro.signal_concurrent(True)
        elif mystrategy:
            cerebro.addstrategy(mystrategy)

        # Set our desired cash start
        cerebro.broker.setcash(100000.0)
        # 配置滑点为0.01%
        cerebro.broker.set_slippage_perc(perc=0.0001)
        # Add a FixedSize sizer according to the stake
        cerebro.addsizer(bt.sizers.FixedSize, stake=100)
        # Set the commission
        comminfo = ACommission()
        cerebro.broker.addcommissioninfo(comminfo)

        # 添加分析指标
        # 返回年初至年末的年度收益率
        cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn')
        # 计算最大回撤相关指标
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown')
        # 计算年化收益：日度收益
        cerebro.addanalyzer(bt.analyzers.Returns, _name='_Returns', tann=252)
        # 计算年化夏普比率：日度收益
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio', timeframe=bt.TimeFrame.Days, annualize=True, riskfreerate=0) # 计算夏普比率
        
        result = cerebro.run()

        # 常用指标提取
        analyzer = {}
        # 提取年化收益
        analyzer['年化收益率（%)'] = result[0].analyzers._Returns.get_analysis()['rnorm100']
        # 提取最大回撤
        analyzer['最大回撤（%)'] = result[0].analyzers._DrawDown.get_analysis()['max']['drawdown'] * (-1)
        # 提取夏普比率
        analyzer['夏普比率'] = result[0].analyzers._SharpeRatio.get_analysis()['sharperatio']
        print(f'{_id}: {analyzer}')
        avg_AnnualReturn += analyzer['年化收益率（%)']
        avg_DrawDown += analyzer['最大回撤（%)']
        avg_SharpeRatio += analyzer['夏普比率']

        cnt += 1
        i += 1
        
    print('--------------------------------------------')
    print(f'平均年化收益率（%): {avg_AnnualReturn/cnt}')
    print(f'平均最大回撤（%): {avg_DrawDown/cnt}')
    print(f'平均夏普比率: {avg_SharpeRatio/cnt}')
        

if __name__ == "__main__":
    evaluate(50, '20230101', '20231231')

