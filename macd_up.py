from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

import ipdb

# create A股 commission 
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

# create a signal
class MacdUpSignal(bt.Indicator):
    lines = ('signal',)

    def __init__(self):
        self.macd = bt.indicators.MACDHisto()
        self.bolling = bt.indicators.BollingerBandsPct()
        
    def next(self):
        if (self.macd.lines.histo[0]>self.macd.lines.histo[-1] and self.macd.lines.histo[-1]>self.macd.lines.histo[-2]) and \
            self.data.lines.close[0]>self.bolling[0]:
             self.line[0] = 1
        else:
             self.line[0] = -1

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
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

    # Add the Data Feed to Cerebro
    cerebro.adddata(data, name='601127')

    # add benchmark 沪深300
    hushen300 = bt.feeds.GenericCSVData(
        dataname='./000300.csv',
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
    cerebro.adddata(hushen300, name='hs300')
    cerebro.addobserver(bt.observers.Benchmark, data=hushen300)
    cerebro.addobserver(bt.observers.TimeReturn)

    # Add a signal
    cerebro.add_signal(bt.SIGNAL_LONG, MacdUpSignal)
    cerebro.signal_accumulate(False)
    cerebro.signal_concurrent(True)
    # 添加要监控的指标
    cerebro.addindicator(bt.indicators.MACDHisto)
    cerebro.addindicator(bt.indicators.BollingerBandsPct)

    # Set our desired cash start
    cerebro.broker.setcash(10000.0)
    # 配置滑点为0.01%
    cerebro.broker.set_slippage_perc(perc=0.0001)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    # Set the commission
    comminfo = ACommission()
    cerebro.broker.addcommissioninfo(comminfo)
    # cerebro.broker.setcommission(commission=2.5, commtype='fixed')

    # Print out the starting conditions
    start_value = cerebro.broker.getvalue()

    # 添加分析指标
    # 返回年初至年末的年度收益率
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn')
    # 计算最大回撤相关指标
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown')
    # 计算年化收益：日度收益
    cerebro.addanalyzer(bt.analyzers.Returns, _name='_Returns', tann=252)
    # 计算年化夏普比率：日度收益
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio', timeframe=bt.TimeFrame.Days, annualize=True, riskfreerate=0) # 计算夏普比率
    # 返回收益率时序
    # cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')

    # Run over everything
    result = cerebro.run()

    # Print out the final result
    print("--------------- start Portfolio Value -----------------")
    print('start Portfolio Value: %.2f' % start_value)
    print("--------------- Final Portfolio Value -----------------")
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # 常用指标提取
    analyzer = {}
    # 提取年化收益
    analyzer['年化收益率'] = result[0].analyzers._Returns.get_analysis()['rnorm']
    analyzer['年化收益率（%)'] = result[0].analyzers._Returns.get_analysis()['rnorm100']
    # 提取最大回撤
    analyzer['最大回撤（%)'] = result[0].analyzers._DrawDown.get_analysis()['max']['drawdown'] * (-1)
    # 提取夏普比率
    analyzer['夏普比率'] = result[0].analyzers._SharpeRatio.get_analysis()['sharperatio']
    print(analyzer)

    # Plot the result
    # cerebro.plot()