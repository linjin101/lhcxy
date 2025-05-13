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
SAR+EMA200策略

这是一个基于抛物线转向指标(SAR)和指数移动平均线(EMA)的纯多头策略：
- 使用EMA 200确定大趋势方向，只在价格位于EMA 200之上时做多
- 当SAR从价格上方翻转到下方时买入
- 当SAR从价格下方翻转到上方时卖出
"""

from core.strategy_template import StrategyTemplate
from core.signal_types import BUY, SELL, OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT, CLOSE_ALL
import pandas as pd
import numpy as np


class SarEmaStrategy(StrategyTemplate):
    """
    SAR+EMA200纯多头策略

    使用EMA 200作为趋势过滤器，并使用SAR指标生成入场和出场信号
    - 价格在EMA 200上方，SAR从上穿下，产生做多信号
    - SAR从下穿上，产生平多信号

    SAR指标适合跟踪趋势性行情，EMA 200过滤掉大部分弱趋势市场
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
        self.ema_period = config.get('ema_period', 200)  # EMA周期，默认200
        self.sar_acceleration = config.get('sar_acceleration', 0.02)  # SAR加速因子，默认0.02
        self.sar_maximum = config.get('sar_maximum', 0.2)  # SAR最大步长，默认0.2

        # 记录策略信息
        self.logger.info(f"初始化SAR+EMA200策略，EMA周期: {self.ema_period}, "
                         f"SAR加速因子: {self.sar_acceleration}, SAR最大步长: {self.sar_maximum}, "
                         )

    def calculate_indicators(self, df):
        """
        计算技术指标：SAR和EMA 200

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
        indicators_df['ema200'] = indicators_df['close'].ewm(span=self.ema_period, adjust=False).mean()

        # 计算SAR指标
        try:
            # 初始化SAR数组
            sar = np.zeros(len(indicators_df))
            is_uptrend = np.zeros(len(indicators_df), dtype=bool)

            # 设置初始值
            # 假设开始是下降趋势，SAR在第一根K线的最高价上方
            is_uptrend[0] = False
            sar[0] = indicators_df['high'].iloc[0]

            # 记录极值点
            extreme_point = indicators_df['low'].iloc[0]

            # 当前加速因子
            acceleration_factor = self.sar_acceleration

            for i in range(1, len(indicators_df)):
                # 上一个SAR值
                prev_sar = sar[i - 1]

                # 计算当前的SAR值
                if is_uptrend[i - 1]:  # 如果前一周期是上升趋势
                    # SAR值计算 = 前一周期的SAR + AF * (EP - 前一周期的SAR)
                    sar[i] = prev_sar + acceleration_factor * (extreme_point - prev_sar)

                    # 确保SAR不高于前两个周期的最低价
                    if i > 1:
                        sar[i] = min(sar[i], indicators_df['low'].iloc[i - 1], indicators_df['low'].iloc[i - 2])

                    # 检查趋势是否转变
                    if indicators_df['low'].iloc[i] < sar[i]:
                        # 趋势转为下降
                        is_uptrend[i] = False
                        sar[i] = extreme_point  # SAR值设为之前的极值点
                        extreme_point = indicators_df['high'].iloc[i]  # 重置极值点
                        acceleration_factor = self.sar_acceleration  # 重置加速因子
                    else:
                        # 维持上升趋势
                        is_uptrend[i] = True
                        # 如果创新高，更新极值点和加速因子
                        if indicators_df['high'].iloc[i] > extreme_point:
                            extreme_point = indicators_df['high'].iloc[i]
                            acceleration_factor = min(acceleration_factor + self.sar_acceleration, self.sar_maximum)
                else:  # 如果前一周期是下降趋势
                    # SAR值计算
                    sar[i] = prev_sar + acceleration_factor * (extreme_point - prev_sar)

                    # 确保SAR不低于前两个周期的最高价
                    if i > 1:
                        sar[i] = max(sar[i], indicators_df['high'].iloc[i - 1], indicators_df['high'].iloc[i - 2])

                    # 检查趋势是否转变
                    if indicators_df['high'].iloc[i] > sar[i]:
                        # 趋势转为上升
                        is_uptrend[i] = True
                        sar[i] = extreme_point  # SAR值设为之前的极值点
                        extreme_point = indicators_df['low'].iloc[i]  # 重置极值点
                        acceleration_factor = self.sar_acceleration  # 重置加速因子
                    else:
                        # 维持下降趋势
                        is_uptrend[i] = False
                        # 如果创新低，更新极值点和加速因子
                        if indicators_df['low'].iloc[i] < extreme_point:
                            extreme_point = indicators_df['low'].iloc[i]
                            acceleration_factor = min(acceleration_factor + self.sar_acceleration, self.sar_maximum)

            # 将计算结果添加到DataFrame
            indicators_df['sar'] = sar
            indicators_df['sar_is_uptrend'] = is_uptrend

        except Exception as e:
            self.logger.error(f"计算SAR指标时出错: {e}")
            return df

        self.logger.info(f"计算完成SAR和EMA200指标")
        return indicators_df

    def generate_signals(self, df):
        """
        生成交易信号

        策略逻辑：
        - 价格在EMA 200上方，SAR从上方翻转到下方(sar_is_uptrend从False变为True)，买入信号
        - SAR从下方翻转到上方(sar_is_uptrend从True变为False)，卖出信号

        Args:
            df: 包含技术指标的K线数据DataFrame

        Returns:
            str: 交易信号，BUY, SELL, None
        """
        if df is None or df.empty or 'ema200' not in df.columns or 'sar_is_uptrend' not in df.columns:
            return None

        # 确保有足够的数据
        if len(df) < 3:
            self.logger.warning("数据不足，无法生成SAR翻转信号，至少需要3根K线")
            return None

        # 获取前前一根、前一根和最新K线数据
        prev_prev = df.iloc[-3]  # 前前一根K线
        prev = df.iloc[-2]  # 前一根K线
        latest = df.iloc[-1]  # 最新K线

        # 检查sar_is_uptrend的变化
        # 由False变为True意味着SAR从价格上方翻转到下方（做多信号）
        # 由True变为False意味着SAR从价格下方翻转到上方（平多信号）

        # 判断趋势翻转情况和EMA 200趋势
        price_above_ema = prev['close'] > prev['ema200']  # 价格是否在EMA 200上方

        # SAR从上方翻转到下方 (做多信号) - 通过sar_is_uptrend由False变为True判断
        sar_buy_signal = prev['sar_is_uptrend'] and not prev_prev['sar_is_uptrend']

        # SAR从下方翻转到上方 (平多信号) - 通过sar_is_uptrend由True变为False判断
        sar_sell_signal = not prev['sar_is_uptrend'] and prev_prev['sar_is_uptrend']

        # 仅做多策略
        # 买入条件：价格在EMA 200上方，且SAR从上方翻转到下方
        if sar_buy_signal and price_above_ema:
            self.logger.info(f"价格在EMA 200上方，SAR从上方翻转到下方，生成买入信号，"
                                 f"前收盘价:{prev['close']}, EMA200:{prev['ema200']}, SAR:{prev['sar']}")
            return OPEN_LONG

        # 卖出条件：SAR从下方翻转到上方
        elif sar_sell_signal:
            self.logger.info(f"SAR从下方翻转到上方，生成卖出信号，前SAR:{prev['sar']}")
            return CLOSE_LONG
