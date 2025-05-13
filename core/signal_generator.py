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
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Optional, Any, Tuple

class BaseSignalGenerator(ABC):
    """
    信号生成器基类：连接因子计算和交易执行的标准化接口
    
    所有信号生成器都应继承此类并实现相应方法
    """
    
    def __init__(self, name: str):
        """
        初始化信号生成器
        
        Args:
            name: 信号生成器名称
        """
        self.name = name
    
    @abstractmethod
    def generate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        生成交易信号，必须由子类实现
        
        Args:
            df: 市场数据DataFrame，应已包含所需指标
            **kwargs: 其他参数
            
        Returns:
            包含信号列的DataFrame
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        验证数据是否满足信号生成的要求
        
        Args:
            df: 输入的DataFrame
            
        Returns:
            bool: 数据是否有效
        """
        return not df.empty
    
    def __str__(self) -> str:
        """信号生成器描述"""
        return f"{self.name} 信号生成器"
    
    def get_last_signal(self, df: pd.DataFrame, signal_column: str = 'signal') -> Optional[str]:
        """
        获取最新的交易信号
        
        Args:
            df: 包含信号列的DataFrame
            signal_column: 信号列名
            
        Returns:
            最新的交易信号或None
        """
        if df.empty or signal_column not in df.columns:
            return None
        
        last_signal = df.iloc[-1][signal_column]
        return last_signal if pd.notna(last_signal) else None


class CrossoverSignalGenerator(BaseSignalGenerator):
    """
    交叉信号生成器：用于生成基于两条线交叉的信号
    
    例如移动平均线交叉、MACD金叉死叉等
    """
    
    def __init__(self, fast_column: str, slow_column: str, signal_column: str = 'signal'):
        """
        初始化交叉信号生成器
        
        Args:
            fast_column: 快线列名
            slow_column: 慢线列名
            signal_column: 生成的信号列名
        """
        super().__init__(f"Crossover_{fast_column}_{slow_column}")
        self.fast_column = fast_column
        self.slow_column = slow_column
        self.signal_column = signal_column
    
    def generate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        生成基于交叉的交易信号
        
        Args:
            df: 市场数据DataFrame，必须包含fast_column和slow_column
            **kwargs: 其他参数
            
        Returns:
            添加了信号列的DataFrame
        """
        if not self.validate_data(df):
            return df
        
        # 检查必要的列是否存在
        if self.fast_column not in df.columns or self.slow_column not in df.columns:
            raise ValueError(f"数据缺少必要的列: {self.fast_column} 或 {self.slow_column}")
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 计算前一周期的快线和慢线
        result_df[f'{self.fast_column}_prev'] = result_df[self.fast_column].shift(1)
        result_df[f'{self.slow_column}_prev'] = result_df[self.slow_column].shift(1)
        
        # 初始化信号列
        result_df[self.signal_column] = None
        
        # 生成交叉信号
        # 金叉：前一周期快线低于慢线，当前周期快线高于慢线
        golden_cross = (result_df[f'{self.fast_column}_prev'] < result_df[f'{self.slow_column}_prev']) & \
                       (result_df[self.fast_column] > result_df[self.slow_column])
        
        # 死叉：前一周期快线高于慢线，当前周期快线低于慢线
        death_cross = (result_df[f'{self.fast_column}_prev'] > result_df[f'{self.slow_column}_prev']) & \
                      (result_df[self.fast_column] < result_df[self.slow_column])
        
        # 设置信号
        result_df.loc[golden_cross, self.signal_column] = "BUY"
        result_df.loc[death_cross, self.signal_column] = "SELL"
        
        # 删除临时计算列
        result_df = result_df.drop(columns=[f'{self.fast_column}_prev', f'{self.slow_column}_prev'])
        
        return result_df


class ThresholdSignalGenerator(BaseSignalGenerator):
    """
    阈值信号生成器：用于生成基于指标值超过特定阈值的信号
    
    例如RSI超买超卖、布林带突破等
    """
    
    def __init__(self, indicator_column: str, upper_threshold: float = None, 
                 lower_threshold: float = None, signal_column: str = 'signal'):
        """
        初始化阈值信号生成器
        
        Args:
            indicator_column: 指标列名
            upper_threshold: 上阈值，指标值超过此值产生卖出信号
            lower_threshold: 下阈值，指标值低于此值产生买入信号
            signal_column: 生成的信号列名
        """
        super().__init__(f"Threshold_{indicator_column}")
        self.indicator_column = indicator_column
        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold
        self.signal_column = signal_column
    
    def generate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        生成基于阈值的交易信号
        
        Args:
            df: 市场数据DataFrame，必须包含indicator_column
            **kwargs: 其他参数
            
        Returns:
            添加了信号列的DataFrame
        """
        if not self.validate_data(df):
            return df
        
        # 检查必要的列是否存在
        if self.indicator_column not in df.columns:
            raise ValueError(f"数据缺少必要的列: {self.indicator_column}")
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 初始化信号列
        result_df[self.signal_column] = None
        
        # 生成阈值信号
        # 仅在从下方穿越阈值时生成信号，避免频繁交易
        if self.upper_threshold is not None:
            # 计算前一周期的指标值
            prev_indicator = result_df[self.indicator_column].shift(1)
            
            # 上穿上阈值：前一周期低于阈值，当前周期高于阈值
            upper_cross = (prev_indicator < self.upper_threshold) & \
                          (result_df[self.indicator_column] >= self.upper_threshold)
            
            # 设置卖出信号
            result_df.loc[upper_cross, self.signal_column] = "SELL"
        
        if self.lower_threshold is not None:
            # 计算前一周期的指标值（如果上面已经计算过，这里会重用）
            if 'prev_indicator' not in locals():
                prev_indicator = result_df[self.indicator_column].shift(1)
            
            # 下穿下阈值：前一周期高于阈值，当前周期低于阈值
            lower_cross = (prev_indicator > self.lower_threshold) & \
                          (result_df[self.indicator_column] <= self.lower_threshold)
            
            # 设置买入信号
            result_df.loc[lower_cross, self.signal_column] = "BUY"
        
        return result_df


class PatternSignalGenerator(BaseSignalGenerator):
    """
    模式信号生成器：用于识别特定价格模式并生成信号
    
    例如头肩顶、双顶双底、三重顶底等
    """
    
    def __init__(self, pattern_type: str, signal_column: str = 'signal'):
        """
        初始化模式信号生成器
        
        Args:
            pattern_type: 模式类型，如'head_shoulders', 'double_top', 'triple_bottom'等
            signal_column: 生成的信号列名
        """
        super().__init__(f"Pattern_{pattern_type}")
        self.pattern_type = pattern_type
        self.signal_column = signal_column
    
    def generate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        生成基于价格模式的交易信号
        
        Args:
            df: 市场数据DataFrame
            **kwargs: 其他参数
            
        Returns:
            添加了信号列的DataFrame
        """
        if not self.validate_data(df):
            return df
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 初始化信号列
        result_df[self.signal_column] = None
        
        # 根据模式类型识别价格模式并生成信号
        if self.pattern_type == 'head_shoulders':
            # 头肩顶模式识别逻辑（简化示例）
            # 实际实现中需要更复杂的算法
            pass
            
        elif self.pattern_type == 'double_top':
            # 双顶模式识别逻辑
            pass
            
        elif self.pattern_type == 'double_bottom':
            # 双底模式识别逻辑
            pass
            
        # 可以添加更多模式识别方法
        
        return result_df


class CompositeSignalGenerator(BaseSignalGenerator):
    """
    组合信号生成器：组合多个信号生成器，根据一定的规则合并信号
    
    允许用户将多个信号源组合为一个最终信号
    """
    
    def __init__(self, generators: List[BaseSignalGenerator], method: str = 'unanimous', 
                 signal_column: str = 'signal'):
        """
        初始化组合信号生成器
        
        Args:
            generators: 信号生成器列表
            method: 信号合并方法，可选值:
                - 'unanimous': 所有生成器产生相同信号时才生成最终信号
                - 'majority': 多数生成器产生相同信号时生成最终信号
                - 'any': 任何生成器产生信号时都生成最终信号，优先级: BUY > SELL > None
            signal_column: 生成的信号列名
        """
        super().__init__("Composite")
        self.generators = generators
        self.method = method
        self.signal_column = signal_column
    
    def generate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        生成组合信号
        
        Args:
            df: 市场数据DataFrame
            **kwargs: 其他参数
            
        Returns:
            添加了信号列的DataFrame
        """
        if not self.validate_data(df):
            return df
        
        # 复制DataFrame避免修改原始数据
        result_df = df.copy()
        
        # 收集所有生成器的信号
        all_signals = []
        for generator in self.generators:
            # 生成信号
            signal_df = generator.generate(df, **kwargs)
            # 获取最新信号
            last_signal = generator.get_last_signal(signal_df)
            all_signals.append(last_signal)
        
        # 合并信号
        final_signal = None
        
        if self.method == 'unanimous':
            # 所有非None信号必须一致
            non_none_signals = [s for s in all_signals if s is not None]
            if non_none_signals and all(s == non_none_signals[0] for s in non_none_signals):
                final_signal = non_none_signals[0]
                
        elif self.method == 'majority':
            # 统计每种信号的数量
            signal_counts = {}
            for signal in all_signals:
                if signal is not None:
                    if signal not in signal_counts:
                        signal_counts[signal] = 0
                    signal_counts[signal] += 1
            
            # 找出最多的信号类型
            if signal_counts:
                max_count = max(signal_counts.values())
                max_signals = [s for s, count in signal_counts.items() if count == max_count]
                # 如果有多个信号票数相同，优先选择BUY
                if "BUY" in max_signals:
                    final_signal = "BUY"
                elif "SELL" in max_signals:
                    final_signal = "SELL"
                else:
                    final_signal = max_signals[0]
        
        elif self.method == 'any':
            # 任何信号都接受，优先级：BUY > SELL > None
            if "BUY" in all_signals:
                final_signal = "BUY"
            elif "SELL" in all_signals:
                final_signal = "SELL"
        
        # 在最新行添加最终信号
        if not result_df.empty:
            result_df.loc[result_df.index[-1], self.signal_column] = final_signal
        
        return result_df


# 工厂函数，用于创建信号生成器
def create_signal_generator(config: Dict[str, Any]) -> BaseSignalGenerator:
    """
    根据配置创建信号生成器
    
    Args:
        config: 信号生成器配置，必须包含'type'字段
        
    Returns:
        创建的信号生成器实例
        
    Raises:
        ValueError: 不支持的信号生成器类型
    """
    generator_type = config.get('type')
    
    if generator_type == 'crossover':
        return CrossoverSignalGenerator(
            fast_column=config.get('fast_column'),
            slow_column=config.get('slow_column'),
            signal_column=config.get('signal_column', 'signal')
        )
        
    elif generator_type == 'threshold':
        return ThresholdSignalGenerator(
            indicator_column=config.get('indicator_column'),
            upper_threshold=config.get('upper_threshold'),
            lower_threshold=config.get('lower_threshold'),
            signal_column=config.get('signal_column', 'signal')
        )
        
    elif generator_type == 'pattern':
        return PatternSignalGenerator(
            pattern_type=config.get('pattern_type'),
            signal_column=config.get('signal_column', 'signal')
        )
        
    elif generator_type == 'composite':
        # 创建子生成器
        sub_generators = [create_signal_generator(sub_config) 
                         for sub_config in config.get('generators', [])]
        
        return CompositeSignalGenerator(
            generators=sub_generators,
            method=config.get('method', 'unanimous'),
            signal_column=config.get('signal_column', 'signal')
        )
        
    else:
        raise ValueError(f"不支持的信号生成器类型: {generator_type}") 