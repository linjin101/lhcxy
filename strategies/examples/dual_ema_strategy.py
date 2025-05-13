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
双均线交叉策略

这是一个基于两条指数移动平均线(EMA)的交叉策略：
- 当快线(EMA20)上穿慢线(EMA60)时买入（金叉）
- 当快线(EMA20)下穿慢线(EMA60)时卖出（死叉）

双均线交叉策略能够有效捕捉趋势转变点，适合中长期趋势交易
"""

from core.strategy_template import StrategyTemplate
from core.signal_types import BUY, SELL, OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT
import pandas as pd
import numpy as np


class DualEMAStrategy(StrategyTemplate):
    """
    双均线交叉策略

    使用两条不同周期的EMA均线生成交易信号:
    - 快线上穿慢线，生成开多信号（金叉）
    - 快线下穿慢线，生成开空信号（死叉）

    双均线交叉能够有效过滤市场噪音，捕捉中长期趋势变化
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
        self.fast_ema_period = config.get('fast_ema_period', 20)  # 快线EMA周期，默认20
        self.slow_ema_period = config.get('slow_ema_period', 60)  # 慢线EMA周期，默认60
        self.trade_direction = config.get('trade_direction', 'both')  # 交易方向，默认双向交易

        # 记录策略信息
        self.logger.info(f"初始化双均线交叉策略，快线周期: {self.fast_ema_period}, "
                         f"慢线周期: {self.slow_ema_period}, 交易方向: {self.trade_direction}")

    def calculate_indicators(self, df):
        """
        计算技术指标：两条指数移动平均线

        Args:
            df: K线数据DataFrame

        Returns:
            添加了技术指标的DataFrame
        """
        if df is None or df.empty or len(df) < self.slow_ema_period:
            self.logger.warning(f"数据不足，无法计算{self.slow_ema_period}周期EMA")
            return df

        # 复制DataFrame避免修改原始数据
        indicators_df = df.copy()

        # 计算快线EMA
        indicators_df['fast_ema'] = indicators_df['close'].ewm(span=self.fast_ema_period, adjust=False).mean()

        # 计算慢线EMA
        indicators_df['slow_ema'] = indicators_df['close'].ewm(span=self.slow_ema_period, adjust=False).mean()

        self.logger.info(f"计算完成双均线指标，快线周期: {self.fast_ema_period}, 慢线周期: {self.slow_ema_period}")
        return indicators_df

    def generate_signals(self, df):
        """
        生成交易信号

        策略逻辑：
        - 快线从下方穿过慢线，根据交易方向生成信号（金叉）:
          - 'only_long': OPEN_LONG
          - 'only_short': CLOSE_SHORT
          - 'both': OPEN_LONG
        - 快线从上方穿过慢线，根据交易方向生成信号（死叉）:
          - 'only_long': CLOSE_LONG
          - 'only_short': OPEN_SHORT
          - 'both': OPEN_SHORT

        Args:
            df: 包含技术指标的K线数据DataFrame

        Returns:
            str: 交易信号，OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT, None
        """
        if df is None or df.empty or 'fast_ema' not in df.columns or 'slow_ema' not in df.columns:
            return None

        # 确保有足够的数据
        if len(df) < 3:
            self.logger.warning("数据不足，无法生成穿越信号，至少需要3根K线")
            return None

        # 获取前前一根、前一根和最新K线数据
        prev_prev = df.iloc[-3]  # 前前一根K线
        prev = df.iloc[-2]  # 前一根K线
        latest = df.iloc[-1]  # 最新K线

        # 无法计算交叉（数据不足）
        if (pd.isna(prev_prev['fast_ema']) or pd.isna(prev_prev['slow_ema']) or
                pd.isna(prev['fast_ema']) or pd.isna(prev['slow_ema']) or
                pd.isna(latest['fast_ema']) or pd.isna(latest['slow_ema'])):
            return None

        # 判断是否发生了均线交叉
        # 金叉：前前一根K线快线在慢线下方，前一根K线快线在慢线上方
        if prev_prev['fast_ema'] < prev_prev['slow_ema'] and prev['fast_ema'] > prev['slow_ema']:
            self.logger.info(f"快线上穿慢线，金叉信号，"
                             f"前快线:{prev['fast_ema']:.2f}，前慢线:{prev['slow_ema']:.2f}")
            
            # 根据交易方向生成信号
            if self.trade_direction == 'only_long':
                self.logger.info("金叉信号，交易方向为only_long，生成开多信号")
                return OPEN_LONG
            elif self.trade_direction == 'only_short':
                self.logger.info("金叉信号，交易方向为only_short，生成平空信号")
                return CLOSE_SHORT
            else:  # 'both'
                self.logger.info("金叉信号，交易方向为both，生成开多信号")
                return OPEN_LONG

        # 死叉：前前一根K线快线在慢线上方，前一根K线快线在慢线下方
        elif prev_prev['fast_ema'] > prev_prev['slow_ema'] and prev['fast_ema'] < prev['slow_ema']:
            self.logger.info(f"快线下穿慢线，死叉信号，"
                             f"前快线:{prev['fast_ema']:.2f}，前慢线:{prev['slow_ema']:.2f}")
            
            # 根据交易方向生成信号
            if self.trade_direction == 'only_long':
                self.logger.info("死叉信号，交易方向为only_long，生成平多信号")
                return CLOSE_LONG
            elif self.trade_direction == 'only_short':
                self.logger.info("死叉信号，交易方向为only_short，生成开空信号")
                return OPEN_SHORT
            else:  # 'both'
                self.logger.info("死叉信号，交易方向为both，生成开空信号")
                return OPEN_SHORT

        # 无穿越，无信号
        return None