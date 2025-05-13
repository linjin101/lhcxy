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
双均线交叉策略示例

这是一个经典的双均线交叉策略，使用快线和慢线的交叉来判断趋势方向：
- 当快线上穿慢线时买入（金叉）
- 当快线下穿慢线时卖出（死叉）

比单均线策略更稳定，减少了假信号
"""

from core.strategy_template import StrategyTemplate
import pandas as pd
import numpy as np

class DualMAStrategy(StrategyTemplate):
    """
    双均线交叉策略
    
    使用快速和慢速移动平均线的交叉来判断趋势方向
    - 快线上穿慢线(金叉)，视为上升趋势，产生买入信号
    - 快线下穿慢线(死叉)，视为下降趋势，产生卖出信号
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
        self.fast_period = config.get('fast_period', 5)  # 快线周期，默认5
        self.slow_period = config.get('slow_period', 20)  # 慢线周期，默认20
        self.ma_type = config.get('ma_type', 'SMA')  # 均线类型，默认为简单移动平均线
        
        # 记录策略信息
        self.logger.info(f"初始化双均线策略，快线周期: {self.fast_period}，慢线周期: {self.slow_period}，均线类型: {self.ma_type}")
    
    def calculate_indicators(self, df):
        """
        计算技术指标：快速和慢速移动平均线
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            添加了技术指标的DataFrame
        """
        if df is None or df.empty or len(df) < max(self.fast_period, self.slow_period):
            self.logger.warning(f"数据不足，无法计算MA指标")
            return df
        
        # 复制DataFrame避免修改原始数据
        indicators_df = df.copy()
        
        # 根据MA类型选择计算方法
        if self.ma_type == 'EMA':
            # 指数移动平均线
            indicators_df['fast_ma'] = indicators_df['close'].ewm(span=self.fast_period, adjust=False).mean()
            indicators_df['slow_ma'] = indicators_df['close'].ewm(span=self.slow_period, adjust=False).mean()
        else:
            # 默认使用简单移动平均线(SMA)
            indicators_df['fast_ma'] = indicators_df['close'].rolling(window=self.fast_period).mean()
            indicators_df['slow_ma'] = indicators_df['close'].rolling(window=self.slow_period).mean()
        
        # 计算快线和慢线的差值，正值表示快线在上，负值表示快线在下
        indicators_df['ma_diff'] = indicators_df['fast_ma'] - indicators_df['slow_ma']
        indicators_df['ma_diff_pct'] = indicators_df['ma_diff'] / indicators_df['slow_ma'] * 100
        
        # 添加前一周期的值，用于判断交叉
        indicators_df['prev_fast_ma'] = indicators_df['fast_ma'].shift(1)
        indicators_df['prev_slow_ma'] = indicators_df['slow_ma'].shift(1)
        indicators_df['prev_ma_diff'] = indicators_df['ma_diff'].shift(1)
        
        self.logger.info(f"计算完成双均线指标，快线: {self.fast_period}，慢线: {self.slow_period}")
        return indicators_df
    
    def generate_signals(self, df):
        """
        生成交易信号
        
        策略逻辑：
        - 快线从下方穿过慢线（金叉），买入信号
        - 快线从上方穿过慢线（死叉），卖出信号
        
        Args:
            df: 包含技术指标的K线数据DataFrame
            
        Returns:
            str: 交易信号，"BUY", "SELL", None
        """
        if df is None or df.empty or 'fast_ma' not in df.columns or 'slow_ma' not in df.columns:
            return None
        
        # 确保有足够的数据
        if len(df) < 3:
            self.logger.warning("数据不足，无法生成穿越信号，至少需要3根K线")
            return None
        
        # 获取前前一根、前一根和最新K线数据
        prev_prev = df.iloc[-3]  # 前前一根K线
        prev = df.iloc[-2]       # 前一根K线
        latest = df.iloc[-1]     # 最新K线（当前已完成的K线）
        
        # 无法计算交叉（数据不足）
        if pd.isna(prev_prev['fast_ma']) or pd.isna(prev_prev['slow_ma']) or pd.isna(prev['fast_ma']) or pd.isna(prev['slow_ma']):
            return None
        
        # 判断是否发生了金叉或死叉
        # 金叉：前前一根K线快线低于慢线，前一根K线快线高于慢线
        if prev_prev['fast_ma'] < prev_prev['slow_ma'] and prev['fast_ma'] > prev['slow_ma']:
            self.logger.info(f"双均线金叉，生成买入信号，前一根K线快线:{prev['fast_ma']}，慢线:{prev['slow_ma']}")
            return "BUY"
            
        # 死叉：前前一根K线快线高于慢线，前一根K线快线低于慢线
        elif prev_prev['fast_ma'] > prev_prev['slow_ma'] and prev['fast_ma'] < prev['slow_ma']:
            self.logger.info(f"双均线死叉，生成卖出信号，前一根K线快线:{prev['fast_ma']}，慢线:{prev['slow_ma']}")
            return "SELL"
            
        # 无交叉，无信号
        return None 