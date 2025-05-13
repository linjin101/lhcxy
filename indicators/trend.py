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

import pandas as pd
import numpy as np
from typing import List, Union, Optional
from indicators.base_indicator import BaseIndicator

class ADX(BaseIndicator):
    """
    平均趋向指数(ADX)指标
    
    用于评估趋势的强度，无论方向是上涨还是下跌
    """
    
    def __init__(self, period: int = 14):
        """
        初始化ADX指标
        
        Args:
            period: 计算周期，默认14
        """
        super().__init__(f"ADX_{period}")
        self.period = period
    
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算ADX指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了ADX、+DI、-DI列的DataFrame
        """
        if not self.validate_dataframe(df):
            raise ValueError("输入DataFrame缺少必要的OHLCV列")
        
        if len(df) < self.period + 1:
            return df  # 数据不足以计算指标
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 计算方向变动
        result_df['high_diff'] = result_df['high'].diff()
        result_df['low_diff'] = result_df['low'].diff()
        
        # 正向方向变动(+DM)
        result_df['plus_dm'] = np.where(
            (result_df['high_diff'] > 0) & (result_df['high_diff'] > result_df['low_diff'].abs()),
            result_df['high_diff'],
            0
        )
        
        # 负向方向变动(-DM)
        result_df['minus_dm'] = np.where(
            (result_df['low_diff'] < 0) & (result_df['low_diff'].abs() > result_df['high_diff']),
            result_df['low_diff'].abs(),
            0
        )
        
        # 计算真实范围(TR)
        high_low = result_df['high'] - result_df['low']
        high_close_prev = (result_df['high'] - result_df['close'].shift(1)).abs()
        low_close_prev = (result_df['low'] - result_df['close'].shift(1)).abs()
        result_df['tr'] = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        
        # 平滑化TR和DM
        result_df['tr_' + str(self.period)] = result_df['tr'].rolling(window=self.period).sum()
        result_df['plus_dm_' + str(self.period)] = result_df['plus_dm'].rolling(window=self.period).sum()
        result_df['minus_dm_' + str(self.period)] = result_df['minus_dm'].rolling(window=self.period).sum()
        
        # 计算+DI和-DI
        result_df['plus_di_' + str(self.period)] = 100 * (result_df['plus_dm_' + str(self.period)] / result_df['tr_' + str(self.period)])
        result_df['minus_di_' + str(self.period)] = 100 * (result_df['minus_dm_' + str(self.period)] / result_df['tr_' + str(self.period)])
        
        # 计算方向指数(DX)
        result_df['dx_' + str(self.period)] = 100 * (
            abs(result_df['plus_di_' + str(self.period)] - result_df['minus_di_' + str(self.period)]) /
            (result_df['plus_di_' + str(self.period)] + result_df['minus_di_' + str(self.period)])
        )
        
        # 计算ADX
        result_df['ADX'] = result_df['dx_' + str(self.period)].rolling(window=self.period).mean()
        
        # 保留结果列，删除中间计算列
        cols_to_keep = ['ADX', 'plus_di_' + str(self.period), 'minus_di_' + str(self.period)]
        for col in cols_to_keep:
            if col != 'ADX':
                new_col = col.replace('plus_di_', '+DI_').replace('minus_di_', '-DI_')
                result_df[new_col] = result_df[col]
        
        # 删除中间计算的列
        cols_to_drop = [col for col in result_df.columns if col not in df.columns and col not in ['ADX', '+DI_' + str(self.period), '-DI_' + str(self.period)]]
        result_df = result_df.drop(columns=cols_to_drop)
        
        return result_df
    
    def get_output_column_names(self) -> List[str]:
        """获取该指标输出的列名列表"""
        return ['ADX', '+DI_' + str(self.period), '-DI_' + str(self.period)]
    
    def get_min_length(self) -> int:
        """获取计算此指标需要的最小数据长度"""
        return 2 * self.period + 1
    
    def get_description(self) -> str:
        """获取指标描述"""
        return f"平均趋向指数(ADX)，周期: {self.period}"



class ParabolicSAR(BaseIndicator):
    """
    抛物线转向系统(Parabolic SAR)
    
    趋势跟踪指标，提供潜在的买入和卖出信号
    """
    
    def __init__(self, acceleration: float = 0.02, maximum: float = 0.2):
        """
        初始化抛物线SAR指标
        
        Args:
            acceleration: 加速因子，默认0.02
            maximum: 最大加速因子，默认0.2
        """
        super().__init__("ParabolicSAR")
        self.acceleration = acceleration
        self.maximum = maximum
    
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算抛物线SAR指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了SAR列的DataFrame
        """
        if not self.validate_dataframe(df):
            raise ValueError("输入DataFrame缺少必要的OHLCV列")
        
        if len(df) < 2:
            return df  # 数据不足以计算指标
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 初始化SAR数组
        sar = np.zeros(len(result_df))
        sar[0] = np.nan
        
        # 初始化加速因子和极值
        af = self.acceleration
        ep = result_df['high'].iloc[0]  # 假设第一个趋势是上涨
        is_uptrend = True
        
        # 计算SAR
        for i in range(1, len(result_df)):
            if is_uptrend:
                # 上涨趋势
                if i == 1:
                    sar[i] = result_df['low'].iloc[0]
                else:
                    sar[i] = sar[i-1] + af * (ep - sar[i-1])
                
                # 检查是否需要反转
                if result_df['low'].iloc[i] < sar[i]:
                    is_uptrend = False
                    sar[i] = ep
                    ep = result_df['low'].iloc[i]
                    af = self.acceleration
                else:
                    # 更新极值和加速因子
                    if result_df['high'].iloc[i] > ep:
                        ep = result_df['high'].iloc[i]
                        af = min(af + self.acceleration, self.maximum)
                    
                    # 确保SAR不高于前两个周期的低点
                    if i >= 2:
                        sar[i] = min(sar[i], result_df['low'].iloc[i-1], result_df['low'].iloc[i-2])
            else:
                # 下跌趋势
                sar[i] = sar[i-1] + af * (ep - sar[i-1])
                
                # 检查是否需要反转
                if result_df['high'].iloc[i] > sar[i]:
                    is_uptrend = True
                    sar[i] = ep
                    ep = result_df['high'].iloc[i]
                    af = self.acceleration
                else:
                    # 更新极值和加速因子
                    if result_df['low'].iloc[i] < ep:
                        ep = result_df['low'].iloc[i]
                        af = min(af + self.acceleration, self.maximum)
                    
                    # 确保SAR不低于前两个周期的高点
                    if i >= 2:
                        sar[i] = max(sar[i], result_df['high'].iloc[i-1], result_df['high'].iloc[i-2])
        
        # 添加到结果DataFrame
        result_df['PSAR'] = sar
        
        return result_df
    
    def get_output_column_names(self) -> List[str]:
        """获取该指标输出的列名列表"""
        return ['PSAR']
    
    def get_min_length(self) -> int:
        """获取计算此指标需要的最小数据长度"""
        return 3  # 需要前两个周期的数据
    
    def get_description(self) -> str:
        """获取指标描述"""
        return f"抛物线转向系统(Parabolic SAR)，加速因子: {self.acceleration}，最大加速因子: {self.maximum}" 