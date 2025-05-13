"""
Python量化实战框架-okx版
这个框架是我们python量化行动家的内容，欢迎大家加入我们的量化行动家，一起玩量化，一起进步
所有将加入行动家社群的同学，框架会定期更新，并且后面会有更多框架上架
微信: coder_v5 （微信联系务必备注来意)
本程序作者: 菜哥

# 框架内容
okx u本位择时策略实盘框架

本框架程序是菜哥原创，并且仅供量化行动家社群的同学使用和阅读，
发现侵权行为，作者将依法追究相关责任，并委托维权骑士进行维权处理，以维护自身合法权益。
若发现有抄袭、篡改、未经授权传播等侵权情况，作者将采取法律手段进行维权
"""

"""
指数移动平均线策略示例

这是一个基于指数移动平均线(EMA)的策略，EMA与简单移动平均线(SMA)相比，更重视近期价格变化：
- 当价格上穿EMA时买入
- 当价格下穿EMA时卖出

EMA对市场变化的反应更为灵敏，适合波动较大的市场环境
"""

from core.strategy_template import StrategyTemplate
from core.signal_types import BUY, SELL, OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT, CLOSE_ALL
import pandas as pd
import numpy as np

class EMAStrategy(StrategyTemplate):
    """
    指数移动平均线策略
    
    使用指数移动平均线(EMA)来判断价格趋势
    - 价格上穿EMA，视为上升趋势，产生买入信号
    - 价格下穿EMA，视为下降趋势，产生卖出信号
    
    EMA相比SMA赋予近期价格更高的权重，能更敏感地反应价格变化
    """
    
    def __init__(self, trader, config):
        """
        初始化策略
        
        Args:
            trader: OkxTrader实例
            config: 策略配置
        """
        super().__init__(trader, config)
        
        # 获取策略参数
        self.ema_period = config.get('ema_period', 20)  # EMA周期，默认20
        
        # 记录策略信息
        self.logger.info(f"初始化EMA策略，周期: {self.ema_period}")
    
    def calculate_indicators(self, df):
        """
        计算技术指标：指数移动平均线
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            添加了技术指标的DataFrame
        """
        if df is None or df.empty or len(df) < self.ema_period:
            self.logger.warning(f"数据不足，无法计算{self.ema_period}周期EMA")
            return df
        
        # 复制DataFrame避免修改原始数据
        indicators_df = df.copy()
        
        # 计算指数移动平均线
        indicators_df['ema'] = indicators_df['close'].ewm(span=self.ema_period, adjust=False).mean()
        
        self.logger.info(f"计算完成EMA指标，周期: {self.ema_period}")
        return indicators_df
    
    def generate_signals(self, df):
        """
        生成交易信号
        
        策略逻辑：
        - 价格从下方穿过EMA，买入信号
        - 价格从上方穿过EMA，卖出信号
        
        Args:
            df: 包含技术指标的K线数据DataFrame
            
        Returns:
            str: 交易信号，"BUY", "SELL", None
        """
        if df is None or df.empty or 'ema' not in df.columns:
            return None
        
        # 确保有足够的数据
        if len(df) < 3:
            self.logger.warning("数据不足，无法生成穿越信号，至少需要3根K线")
            return None
        
        # 获取前前一根、前一根和最新K线数据
        prev_prev = df.iloc[-3]  # 前前一根K线
        prev = df.iloc[-2]       # 前一根K线
        latest = df.iloc[-1]     # 最新K线（当前的k线）
        
        # 无法计算交叉（数据不足）
        if pd.isna(prev_prev['ema']) or pd.isna(prev['ema']) or pd.isna(latest['ema']):
            return None
        
        # 判断是否发生了穿越
        # 上穿：前前一根K线收盘价低于EMA，前一根K线收盘价高于EMA
        if prev_prev['close'] < prev_prev['ema'] and prev['close'] > prev['ema']:
            self.logger.info(f"价格上穿EMA，生成买入信号，前前收盘价:{prev_prev['close']}，前收盘价:{prev['close']}，EMA:{prev['ema']}")
            # return "BUY"
            return BUY
            
        # 下穿：前前一根K线收盘价高于EMA，前一根K线收盘价低于EMA
        elif prev_prev['close'] > prev_prev['ema'] and prev['close'] < prev['ema']:
            self.logger.info(f"价格下穿EMA，生成卖出信号，前前收盘价:{prev_prev['close']}，前收盘价:{prev['close']}，EMA:{prev['ema']}")
            # return "SELL"
            return SELL
            
        # 无穿越，无信号
        return None 