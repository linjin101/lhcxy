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

class SimpleMovingAverage(BaseIndicator):
    """
    简单移动平均线(SMA)指标
    
    计算给定周期的简单移动平均线
    """
    
    def __init__(self, period: int = 20, source_column: str = 'close'):
        """
        初始化SMA指标
        
        Args:
            period: 移动平均周期
            source_column: 计算移动平均的数据列名，默认为'close'
        """
        super().__init__(f"SMA_{period}")
        self.period = period
        self.source_column = source_column
    
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算SMA指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了SMA列的DataFrame
        """
        if not self.validate_dataframe(df):
            raise ValueError("输入DataFrame缺少必要的OHLCV列")
        
        if len(df) < self.period:
            return df  # 数据不足以计算指标
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 计算SMA
        result_df[self.name] = result_df[self.source_column].rolling(window=self.period).mean()
        
        return result_df
    
    def get_min_length(self) -> int:
        """获取计算此指标需要的最小数据长度"""
        return self.period
    
    def get_description(self) -> str:
        """获取指标描述"""
        return f"简单移动平均线(SMA)，周期: {self.period}，数据源: {self.source_column}"


class ExponentialMovingAverage(BaseIndicator):
    """
    指数移动平均线(EMA)指标
    
    计算给定周期的指数移动平均线，相比SMA更重视近期数据
    """
    
    def __init__(self, period: int = 20, source_column: str = 'close'):
        """
        初始化EMA指标
        
        Args:
            period: 移动平均周期
            source_column: 计算移动平均的数据列名，默认为'close'
        """
        super().__init__(f"EMA_{period}")
        self.period = period
        self.source_column = source_column
    
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算EMA指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了EMA列的DataFrame
        """
        if not self.validate_dataframe(df):
            raise ValueError("输入DataFrame缺少必要的OHLCV列")
        
        if len(df) < self.period:
            return df  # 数据不足以计算指标
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 计算EMA
        result_df[self.name] = result_df[self.source_column].ewm(span=self.period, adjust=False).mean()
        
        return result_df
    
    def get_min_length(self) -> int:
        """获取计算此指标需要的最小数据长度"""
        return self.period
    
    def get_description(self) -> str:
        """获取指标描述"""
        return f"指数移动平均线(EMA)，周期: {self.period}，数据源: {self.source_column}"


class WeightedMovingAverage(BaseIndicator):
    """
    加权移动平均线(WMA)指标
    
    计算给定周期的加权移动平均线，根据数据的位置赋予不同权重
    """
    
    def __init__(self, period: int = 20, source_column: str = 'close'):
        """
        初始化WMA指标
        
        Args:
            period: 移动平均周期
            source_column: 计算移动平均的数据列名，默认为'close'
        """
        super().__init__(f"WMA_{period}")
        self.period = period
        self.source_column = source_column
    
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算WMA指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了WMA列的DataFrame
        """
        if not self.validate_dataframe(df):
            raise ValueError("输入DataFrame缺少必要的OHLCV列")
        
        if len(df) < self.period:
            return df  # 数据不足以计算指标
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 计算权重
        weights = np.arange(1, self.period + 1)
        sum_weights = np.sum(weights)
        
        # 计算WMA
        values = result_df[self.source_column].values
        result = []
        
        for i in range(len(values)):
            if i < self.period - 1:
                result.append(np.nan)
            else:
                window_values = values[i - self.period + 1 : i + 1]
                wma = np.sum(window_values * weights) / sum_weights
                result.append(wma)
        
        result_df[self.name] = result
        
        return result_df
    
    def get_min_length(self) -> int:
        """获取计算此指标需要的最小数据长度"""
        return self.period
    
    def get_description(self) -> str:
        """获取指标描述"""
        return f"加权移动平均线(WMA)，周期: {self.period}，数据源: {self.source_column}"


class HullMovingAverage(BaseIndicator):
    """
    Hull移动平均线(HMA)指标
    
    Alan Hull开发的移动平均线，减少滞后性，保持曲线平滑
    """
    
    def __init__(self, period: int = 20, source_column: str = 'close'):
        """
        初始化HMA指标
        
        Args:
            period: 移动平均周期
            source_column: 计算移动平均的数据列名，默认为'close'
        """
        super().__init__(f"HMA_{period}")
        self.period = period
        self.source_column = source_column
    
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算HMA指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了HMA列的DataFrame
        """
        if not self.validate_dataframe(df):
            raise ValueError("输入DataFrame缺少必要的OHLCV列")
        
        if len(df) < self.period:
            return df  # 数据不足以计算指标
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 计算HMA: HMA = WMA(2*WMA(n/2) - WMA(n)), sqrt(n))
        half_period = int(self.period / 2)
        sqrt_period = int(np.sqrt(self.period))
        
        # 计算WMA(n)
        wma_n = pd.Series(
            result_df[self.source_column].rolling(
                window=self.period, 
                win_type='triangular'
            ).mean(), 
            index=result_df.index
        )
        
        # 计算WMA(n/2)
        wma_half = pd.Series(
            result_df[self.source_column].rolling(
                window=half_period, 
                win_type='triangular'
            ).mean(), 
            index=result_df.index
        )
        
        # 计算2*WMA(n/2) - WMA(n)
        raw_hma = 2 * wma_half - wma_n
        
        # 计算最终的HMA
        result_df[self.name] = pd.Series(
            raw_hma.rolling(
                window=sqrt_period, 
                win_type='triangular'
            ).mean(), 
            index=result_df.index
        )
        
        return result_df
    
    def get_min_length(self) -> int:
        """获取计算此指标需要的最小数据长度"""
        return self.period
    
    def get_description(self) -> str:
        """获取指标描述"""
        return f"Hull移动平均线(HMA)，周期: {self.period}，数据源: {self.source_column}"


class MAFactory:
    """
    移动平均线工厂类，用于创建不同类型的移动平均线指标
    """
    
    @staticmethod
    def create(ma_type: str, period: int = 20, source_column: str = 'close') -> BaseIndicator:
        """
        创建指定类型的移动平均线指标
        
        Args:
            ma_type: 移动平均线类型，支持'SMA', 'EMA', 'WMA', 'HMA'
            period: 移动平均周期
            source_column: 计算移动平均的数据列名
            
        Returns:
            BaseIndicator: 创建的移动平均线指标实例
            
        Raises:
            ValueError: 不支持的移动平均线类型
        """
        ma_type = ma_type.upper()
        
        if ma_type == 'SMA':
            return SimpleMovingAverage(period, source_column)
        elif ma_type == 'EMA':
            return ExponentialMovingAverage(period, source_column)
        elif ma_type == 'WMA':
            return WeightedMovingAverage(period, source_column)
        elif ma_type == 'HMA':
            return HullMovingAverage(period, source_column)
        else:
            raise ValueError(f"不支持的移动平均线类型: {ma_type}") 