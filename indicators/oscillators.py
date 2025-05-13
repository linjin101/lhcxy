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

class RSI(BaseIndicator):
    """
    相对强弱指数(RSI)指标
    
    测量价格变动的速度和变化，判断市场超买或超卖状态
    """
    
    def __init__(self, period: int = 14, source_column: str = 'close'):
        """
        初始化RSI指标
        
        Args:
            period: 计算周期，默认14
            source_column: 计算的数据列名，默认为'close'
        """
        super().__init__(f"RSI_{period}")
        self.period = period
        self.source_column = source_column
    
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算RSI指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了RSI列的DataFrame
        """
        if not self.validate_dataframe(df):
            raise ValueError("输入DataFrame缺少必要的OHLCV列")
        
        if len(df) < self.period:
            return df  # 数据不足以计算指标
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 计算价格变化
        delta = result_df[self.source_column].diff()
        
        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均上涨和下跌
        avg_gain = gain.rolling(window=self.period).mean()
        avg_loss = loss.rolling(window=self.period).mean()
        
        # 计算相对强度
        rs = avg_gain / avg_loss
        
        # 计算RSI
        result_df[self.name] = 100 - (100 / (1 + rs))
        
        return result_df
    
    def get_min_length(self) -> int:
        """获取计算此指标需要的最小数据长度"""
        return self.period + 1  # 需要额外一个周期用于计算差值
    
    def get_description(self) -> str:
        """获取指标描述"""
        return f"相对强弱指数(RSI)，周期: {self.period}，数据源: {self.source_column}"


class MACD(BaseIndicator):
    """
    移动平均收敛/发散(MACD)指标
    
    通过计算两个移动平均线之间的差值，判断趋势方向和强度
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, source_column: str = 'close'):
        """
        初始化MACD指标
        
        Args:
            fast_period: 快线周期，默认12
            slow_period: 慢线周期，默认26
            signal_period: 信号线周期，默认9
            source_column: 计算的数据列名，默认为'close'
        """
        super().__init__("MACD")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.source_column = source_column
    
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算MACD指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了MACD、Signal和Histogram列的DataFrame
        """
        if not self.validate_dataframe(df):
            raise ValueError("输入DataFrame缺少必要的OHLCV列")
        
        min_periods = max(self.fast_period, self.slow_period) + self.signal_period
        if len(df) < min_periods:
            return df  # 数据不足以计算指标
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 计算快线和慢线的EMA
        fast_ema = result_df[self.source_column].ewm(span=self.fast_period, adjust=False).mean()
        slow_ema = result_df[self.source_column].ewm(span=self.slow_period, adjust=False).mean()
        
        # 计算MACD线
        result_df['MACD_Line'] = fast_ema - slow_ema
        
        # 计算信号线
        result_df['MACD_Signal'] = result_df['MACD_Line'].ewm(span=self.signal_period, adjust=False).mean()
        
        # 计算直方图
        result_df['MACD_Histogram'] = result_df['MACD_Line'] - result_df['MACD_Signal']
        
        return result_df
    
    def get_output_column_names(self) -> List[str]:
        """获取该指标输出的列名列表"""
        return ['MACD_Line', 'MACD_Signal', 'MACD_Histogram']
    
    def get_min_length(self) -> int:
        """获取计算此指标需要的最小数据长度"""
        return max(self.fast_period, self.slow_period) + self.signal_period
    
    def get_description(self) -> str:
        """获取指标描述"""
        return (f"移动平均收敛/发散(MACD)，快线周期: {self.fast_period}，"
                f"慢线周期: {self.slow_period}，信号线周期: {self.signal_period}，"
                f"数据源: {self.source_column}")


class Stochastic(BaseIndicator):
    """
    随机震荡指标(KDJ)
    
    测量当前价格相对于指定时期内价格区间的位置，判断超买或超卖状态
    """
    
    def __init__(self, k_period: int = 14, d_period: int = 3, j_period: int = 3):
        """
        初始化KDJ指标
        
        Args:
            k_period: K值周期，默认14
            d_period: D值周期，默认3
            j_period: J值周期，默认3
        """
        super().__init__("KDJ")
        self.k_period = k_period
        self.d_period = d_period
        self.j_period = j_period
    
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算KDJ指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了K、D、J列的DataFrame
        """
        if not self.validate_dataframe(df):
            raise ValueError("输入DataFrame缺少必要的OHLCV列")
        
        min_periods = self.k_period + max(self.d_period, self.j_period)
        if len(df) < min_periods:
            return df  # 数据不足以计算指标
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 计算最高价和最低价的滚动窗口
        high_roll = result_df['high'].rolling(window=self.k_period)
        low_roll = result_df['low'].rolling(window=self.k_period)
        
        # 计算周期内的最高价和最低价
        highest_high = high_roll.max()
        lowest_low = low_roll.min()
        
        # 计算K值（快速随机指标）
        result_df['KDJ_K'] = 100 * ((result_df['close'] - lowest_low) / (highest_high - lowest_low))
        
        # 计算D值（K的移动平均）
        result_df['KDJ_D'] = result_df['KDJ_K'].rolling(window=self.d_period).mean()
        
        # 计算J值（3D - 2K）
        result_df['KDJ_J'] = 3 * result_df['KDJ_D'] - 2 * result_df['KDJ_K']
        
        return result_df
    
    def get_output_column_names(self) -> List[str]:
        """获取该指标输出的列名列表"""
        return ['KDJ_K', 'KDJ_D', 'KDJ_J']
    
    def get_min_length(self) -> int:
        """获取计算此指标需要的最小数据长度"""
        return self.k_period + max(self.d_period, self.j_period)
    
    def get_description(self) -> str:
        """获取指标描述"""
        return f"随机震荡指标(KDJ)，K值周期: {self.k_period}，D值周期: {self.d_period}，J值周期: {self.j_period}"


class BollingerBands(BaseIndicator):
    """
    布林带指标
    
    利用统计学中的标准差，计算价格的上下轨道，判断价格波动范围
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0, source_column: str = 'close'):
        """
        初始化布林带指标
        
        Args:
            period: 移动平均周期，默认20
            std_dev: 标准差倍数，默认2.0
            source_column: 计算的数据列名，默认为'close'
        """
        super().__init__("BollingerBands")
        self.period = period
        self.std_dev = std_dev
        self.source_column = source_column
    
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算布林带指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了Middle、Upper和Lower列的DataFrame
        """
        if not self.validate_dataframe(df):
            raise ValueError("输入DataFrame缺少必要的OHLCV列")
        
        if len(df) < self.period:
            return df  # 数据不足以计算指标
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 计算中轨（移动平均线）
        result_df['BB_Middle'] = result_df[self.source_column].rolling(window=self.period).mean()
        
        # 计算标准差
        result_df['BB_StdDev'] = result_df[self.source_column].rolling(window=self.period).std(ddof=0)
        
        # 计算上轨和下轨
        result_df['BB_Upper'] = result_df['BB_Middle'] + (self.std_dev * result_df['BB_StdDev'])
        result_df['BB_Lower'] = result_df['BB_Middle'] - (self.std_dev * result_df['BB_StdDev'])
        
        # 计算宽度
        result_df['BB_Width'] = (result_df['BB_Upper'] - result_df['BB_Lower']) / result_df['BB_Middle']
        
        return result_df
    
    def get_output_column_names(self) -> List[str]:
        """获取该指标输出的列名列表"""
        return ['BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width', 'BB_StdDev']
    
    def get_min_length(self) -> int:
        """获取计算此指标需要的最小数据长度"""
        return self.period
    
    def get_description(self) -> str:
        """获取指标描述"""
        return f"布林带指标，周期: {self.period}，标准差倍数: {self.std_dev}，数据源: {self.source_column}"


class ATR(BaseIndicator):
    """
    平均真实范围(ATR)指标
    
    测量市场波动性，不考虑价格方向
    """
    
    def __init__(self, period: int = 14):
        """
        初始化ATR指标
        
        Args:
            period: 计算周期，默认14
        """
        super().__init__(f"ATR_{period}")
        self.period = period
    
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算ATR指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了ATR列的DataFrame
        """
        if not self.validate_dataframe(df):
            raise ValueError("输入DataFrame缺少必要的OHLCV列")
        
        if len(df) < self.period:
            return df  # 数据不足以计算指标
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 计算真实范围(TR)
        high_low = result_df['high'] - result_df['low']
        high_close_prev = abs(result_df['high'] - result_df['close'].shift(1))
        low_close_prev = abs(result_df['low'] - result_df['close'].shift(1))
        
        # 真实范围取三者的最大值
        tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        
        # 计算ATR
        result_df[self.name] = tr.rolling(window=self.period).mean()
        
        return result_df
    
    def get_min_length(self) -> int:
        """获取计算此指标需要的最小数据长度"""
        return self.period + 1  # 需要前一个周期的收盘价
    
    def get_description(self) -> str:
        """获取指标描述"""
        return f"平均真实范围(ATR)，周期: {self.period}" 