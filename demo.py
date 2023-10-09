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

# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)

        # Indicators for the plotting show
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25, plot=False)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25, subplot=False)
        bt.indicators.StochasticSlow(self.datas[0], plot=False)
        self.macd = bt.indicators.MACDHisto(self.datas[0], plot=True)
        rsi = bt.indicators.RSI(self.datas[0], plot=False)
        bt.indicators.SmoothedMovingAverage(rsi, period=10, plot=False)
        bt.indicators.ATR(self.datas[0], plot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0]:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(exectype=bt.Order.Market)

        else:

            if self.dataclose[0] < self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell(exectype=bt.Order.Market)


if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    data = bt.feeds.GenericCSVData(
        dataname='./601127.csv',

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
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # 添加分析指标
    # 返回年初至年末的年度收益率
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn')
    # 计算最大回撤相关指标
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown')
    # 计算年化收益：日度收益
    cerebro.addanalyzer(bt.analyzers.Returns, _name='_Returns', tann=252)
    # 计算年化夏普比率：日度收益
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio', timeframe=bt.TimeFrame.Days, annualize=True, riskfreerate=0) # 计算夏普比率
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='_SharpeRatio_A')
    # 返回收益率时序
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')

    # Run over everything
    result = cerebro.run()

    # Print out the final result
    print("--------------- start Portfolio Value -----------------")
    print('start Portfolio Value: %.2f' % start_value)
    print("--------------- Final Portfolio Value -----------------")
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 提取分析结果
    print("--------------- AnnualReturn -----------------")
    print(result[0].analyzers._AnnualReturn.get_analysis())
    print("--------------- DrawDown -----------------")
    print(result[0].analyzers._DrawDown.get_analysis())
    print("--------------- Returns -----------------")
    print(result[0].analyzers._Returns.get_analysis())
    print("--------------- SharpeRatio -----------------")
    print(result[0].analyzers._SharpeRatio.get_analysis())
    print("--------------- SharpeRatio_A -----------------")
    print(result[0].analyzers._SharpeRatio_A.get_analysis())

    # Plot the result
    cerebro.plot()