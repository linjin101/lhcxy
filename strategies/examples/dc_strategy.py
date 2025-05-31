"""
唐奇安通道策略

这是一个基于唐奇安通道(Donchian Channel)的趋势跟踪策略：
- 对于双向交易：上轨突破开多，下轨突破开空
- 对于纯多模式：上轨突破开多，下轨突破平多
- 对于纯空模式：下轨突破开空，上轨突破平空

唐奇安通道策略能够有效捕捉趋势突破，适合中长期趋势交易
"""

from core.strategy_template import StrategyTemplate
from core.signal_types import BUY, SELL, OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT
import pandas as pd
import numpy as np


class DCStrategy(StrategyTemplate):
    """
    唐奇安通道策略

    使用唐奇安通道生成交易信号:
    - 价格突破上轨：
      * 纯多模式：开多
      * 纯空模式：平空
      * 双向模式：开多
    - 价格突破下轨：
      * 纯多模式：平多
      * 纯空模式：开空
      * 双向模式：开空

    唐奇安通道能够有效捕捉价格突破，跟踪市场趋势变化
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
        self.channel_period = config.get('channel_period', 20)  # 通道周期，默认20
        self.trade_direction = config.get('trade_direction', 'both')  # 交易方向，默认双向交易
        self.use_middle_exit = config.get('use_middle_exit', False)  # 是否使用中轨作为退出信号
        self.symbol = config.get('symbol')

        # 记录策略信息
        self.logger.info(f"初始化唐奇安通道策略，通道周期: {self.channel_period}, "
                         f"交易方向: {self.trade_direction}, 使用中轨退出: {self.use_middle_exit}")

    def calculate_indicators(self, df):
        """
        计算唐奇安通道指标

        Args:
            df: K线数据DataFrame

        Returns:
            添加了技术指标的DataFrame
        """
        if df is None or df.empty or len(df) < self.channel_period:
            self.logger.warning(f"数据不足，无法计算{self.channel_period}周期唐奇安通道")
            return df

        # 复制DataFrame避免修改原始数据
        indicators_df = df.copy()

        # 计算唐奇安通道上轨（n周期最高价）
        indicators_df['upper_band'] = indicators_df['high'].rolling(window=self.channel_period).max().shift(1)

        # 计算唐奇安通道下轨（n周期最低价）
        indicators_df['lower_band'] = indicators_df['low'].rolling(window=self.channel_period).min().shift(1)

        # 计算唐奇安通道中轨（上轨和下轨的平均值）
        indicators_df['middle_band'] = (indicators_df['upper_band'] + indicators_df['lower_band']) / 2

        self.logger.info(f"计算完成唐奇安通道指标，周期: {self.channel_period}")
        return indicators_df

    def check_middle_band_exit(self, df):
        """
        检查是否触发中轨退出条件

        Args:
            df: 包含技术指标的K线数据DataFrame

        Returns:
            bool: 是否应该退出多头交易
            bool: 是否应该退出空头交易
        """
        if not self.use_middle_exit or df is None or df.empty or len(df) < 3:
            return False, False

        # 使用前一根完成的K线（不是最新的未完成K线）
        prev_k = df.iloc[-2]  # 前一根已完成的K线

        # 检查中轨退出条件
        exit_long = prev_k['close'] < prev_k['middle_band']
        exit_short = prev_k['close'] > prev_k['middle_band']

        if exit_long:
            self.logger.info(f"前一根K线收盘价跌破中轨，触发多头平仓条件")
        if exit_short:
            self.logger.info(f"前一根K线收盘价突破中轨，触发空头平仓条件")

        return exit_long, exit_short

    def generate_signals(self, df):
        """
        生成交易信号

        策略逻辑：
        - 价格突破上轨：
          * 纯多模式(only_long)：开多
          * 纯空模式(only_short)：平空
          * 双向模式(both)：开多
        - 价格突破下轨：
          * 纯多模式(only_long)：平多
          * 纯空模式(only_short)：开空
          * 双向模式(both)：开空

        Args:
            df: 包含技术指标的K线数据DataFrame

        Returns:
            str: 交易信号，OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT, None
        """
        if df is None or df.empty or 'upper_band' not in df.columns or 'lower_band' not in df.columns:
            return None

        # 确保有足够的数据
        if len(df) < 3:
            self.logger.warning("数据不足，无法生成突破信号，至少需要3根K线")
            return None

        # 获取前前一根、前一根和最新K线数据
        prev_prev = df.iloc[-3]  # 前前一根K线
        prev = df.iloc[-2]  # 前一根K线（最新完成的K线）
        latest = df.iloc[-1]  # 最新K线（当前未完成的K线）

        # 无法计算通道（数据不足）
        if pd.isna(prev['upper_band']) or pd.isna(prev['lower_band']):
            return None

        # 获取当前持仓状态（实际应用中应从交易接口获取）
        current_position = self.trader.get_position() if hasattr(self.trader, 'get_position') else None

        # 如果有持仓，检查是否触发中轨退出条件
        if current_position is not None and current_position != 'none' and self.use_middle_exit:
            exit_long, exit_short = self.check_middle_band_exit(df)

            if current_position == 'long' and exit_long:
                return CLOSE_LONG
            elif current_position == 'short' and exit_short:
                return CLOSE_SHORT

        # 判断是否发生了上轨突破
        # 正确的逻辑：前一根K线的高点突破了通道上轨
        upper_break = prev['high'] > prev['upper_band']

        # 判断是否发生了下轨突破
        # 正确的逻辑：前一根K线的低点突破了通道下轨
        lower_break = prev['low'] < prev['lower_band']

        # 处理上轨突破
        if upper_break:
            self.logger.info(f"价格突破上轨，前一根K线最高价:{prev['high']:.2f}，上轨:{prev['upper_band']:.2f}")

            if self.trade_direction == 'only_long':
                # 纯多模式：上轨突破开多
                self.logger.info("上轨突破，交易方向为only_long，生成开多信号")
                return OPEN_LONG
            elif self.trade_direction == 'only_short':
                # 纯空模式：上轨突破平空
                self.logger.info("上轨突破，交易方向为only_short，生成平空信号")
                return CLOSE_SHORT
            else:  # 'both'
                # 双向模式：上轨突破开多
                self.logger.info("上轨突破，交易方向为both，生成开多信号")
                return OPEN_LONG

        # 处理下轨突破
        elif lower_break:
            self.logger.info(f"价格突破下轨，前一根K线最低价:{prev['low']:.2f}，下轨:{prev['lower_band']:.2f}")

            if self.trade_direction == 'only_long':
                # 纯多模式：下轨突破平多
                self.logger.info("下轨突破，交易方向为only_long，生成平多信号")
                return CLOSE_LONG
            elif self.trade_direction == 'only_short':
                # 纯空模式：下轨突破开空
                self.logger.info("下轨突破，交易方向为only_short，生成开空信号")
                return OPEN_SHORT
            else:  # 'both'
                # 双向模式：下轨突破开空
                self.logger.info("下轨突破，交易方向为both，生成开空信号")
                return OPEN_SHORT

        # 无突破，无信号
        return None