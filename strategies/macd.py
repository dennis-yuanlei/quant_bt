import backtrader as bt

class MACDStrategy(bt.Strategy):
    def __init__(self):
        # 初始化MACD指标
        self.macd = bt.indicators.MACD(self.data.close)
        self.signal = bt.indicators.MACDSignal(self.macd)

     # 订单状态通知，买入卖出都是下单  
    def notify_order(self, order): 
        if order.status in [order.Submitted, order.Accepted]: 
            # broker 提交/接受了，买/卖订单则什么都不做  
            return 
        # 检查一个订单是否完成  
        # 注意: 当资金不足时，broker会拒绝订单  
        if order.status in [order.Completed]: 
            if order.isbuy(): 
                self.log( 
                    '已买入, 价格: %.2f, 费用: %.2f, 佣金 %.2f' % 
                    (order.executed.price, 
                    order.executed.value, 
                    order.executed.comm)) 
                self.buyprice = order.executed.price 
                self.buycomm = order.executed.comm 
            elif order.issell(): 
                self.log('已卖出, 价格: %.2f, 费用: %.2f, 佣金 %.2f' % 
                    (order.executed.price, 
                    order.executed.value, 
                    order.executed.comm)) 

            # 记录当前交易数量  
            self.bar_executed = len(self) 
        elif order.status in [order.Canceled, order.Margin, order.Rejected]: 
            self.log('订单取消/保证金不足/拒绝')
        # 其他状态记录为：无挂起订单  
        self.order = None

    # 交易状态通知，一买一卖算交易  
    def notify_trade(self, trade): 
        if not trade.isclosed: 
            return 
        self.log('交易利润, 毛利润 %.2f, 净利润 %.2f' % 
        (trade.pnl, trade.pnlcomm))

    def next(self):
        # 如果MACD线从下向上穿过信号线，且当前无持仓，则买入
        if self.macd.macd[0] > self.signal.signal[0] and self.position.size == 0:
            self.buy()
        # 如果MACD线从上向下穿过信号线，且当前有持仓，则卖出
        elif self.macd.macd[0] < self.signal.signal[0] and self.position.size > 0:
            self.sell()