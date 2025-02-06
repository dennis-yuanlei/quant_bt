import backtrader as bt
from .meta import MetaStrategy

class MACDStrategy(MetaStrategy):
    def __init__(self):
        # 初始化MACD指标
        self.macdhist = bt.indicators.MACDHisto()
        self.macd = self.macdhist.lines.macd
        self.macdsignal = self.macdhist.lines.signal

    def next(self):
        # 如果MACD线从下向上穿过信号线，则买入
        if self.macdhist>0:
            self.buy()
        # 如果MACD线从上向下穿过信号线，且当前有持仓（不允许做空）
        elif self.macdhist<0 and self.position:
            self.sell()