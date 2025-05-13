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
from typing import Dict, List, Union, Optional, Any, Tuple
from core.strategy_template import StrategyTemplate
from core.signal_generator import BaseSignalGenerator, create_signal_generator

class SignalStrategy(StrategyTemplate):
    """
    信号驱动策略类：基于信号生成器框架的策略实现
    
    简化策略开发流程，使用户只需配置信号生成器和技术指标，
    无需手动编写复杂的信号处理逻辑
    """
    
    def __init__(self, trader, config):
        """
        初始化信号策略
        
        Args:
            trader: OkxTrader实例
            config: 策略配置，必须包含signal_generators字段
        """
        super().__init__(trader, config)
        
        # 获取信号生成器配置
        signal_generators_config = config.get('signal_generators', [])
        
        # 创建信号生成器
        self.signal_generators = []
        for gen_config in signal_generators_config:
            try:
                generator = create_signal_generator(gen_config)
                self.signal_generators.append(generator)
                self.logger.info(f"创建信号生成器: {generator.name}")
            except Exception as e:
                self.logger.error(f"创建信号生成器失败: {str(e)}")
        
        # 设置信号列名
        self.signal_column = config.get('signal_column', 'signal')
        
        # 获取技术指标配置
        self.indicators_config = config.get('indicators', [])
        
        # 记录初始化信息
        self.logger.info(f"初始化信号驱动策略，共配置了{len(self.signal_generators)}个信号生成器")
    
    def on_initialize(self):
        """自定义初始化"""
        self.logger.info("信号驱动策略初始化")
        
        # 如果没有配置信号生成器，记录警告
        if not self.signal_generators:
            self.logger.warning("没有配置信号生成器，策略可能无法正常工作")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        根据配置的指标列表计算所有必要的技术指标
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            添加了技术指标的DataFrame
        """
        # 导入计算指标的函数
        from indicators import calculate_indicators
        
        # 确保数据足够
        if df is None or df.empty:
            self.logger.warning("数据不足，无法计算技术指标")
            return df
        
        try:
            # 使用indicators模块计算所有配置的指标
            indicators_df = calculate_indicators(df, self.indicators_config)
            
            indicator_columns = [col for col in indicators_df.columns 
                                if col not in df.columns]
            
            if indicator_columns:
                self.logger.info(f"计算了{len(indicator_columns)}个技术指标: {', '.join(indicator_columns)}")
            else:
                self.logger.warning("未计算任何技术指标")
                
            return indicators_df
            
        except Exception as e:
            self.logger.error(f"计算技术指标时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return df
    
    def generate_signals(self, df: pd.DataFrame) -> str:
        """
        生成交易信号
        
        遍历所有信号生成器，应用它们并组合结果
        
        Args:
            df: 包含技术指标的K线数据DataFrame
            
        Returns:
            str: 最终交易信号，"BUY"(买入), "SELL"(卖出), None(无信号)
        """
        if df is None or df.empty:
            self.logger.warning("数据不足，无法生成信号")
            return None
        
        try:
            # 如果没有信号生成器，返回None
            if not self.signal_generators:
                self.logger.warning("没有配置信号生成器，无法生成信号")
                return None
            
            # 使用第一个信号生成器的信号列名
            signal_column = self.signal_generators[0].signal_column
            
            # 应用所有信号生成器
            result_df = df.copy()
            for generator in self.signal_generators:
                self.logger.info(f"应用信号生成器: {generator.name}")
                result_df = generator.generate(result_df)
            
            # 获取最新的信号
            if not result_df.empty and signal_column in result_df.columns:
                latest_signal = result_df.iloc[-1][signal_column]
                
                # 如果信号是NaN，返回None
                if pd.isna(latest_signal):
                    return None
                
                self.logger.info(f"生成信号: {latest_signal}")
                return latest_signal
            else:
                self.logger.warning(f"未能生成有效信号，信号列'{signal_column}'不存在或数据为空")
                return None
                
        except Exception as e:
            self.logger.error(f"生成信号时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def before_signal_generation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        信号生成前的预处理
        
        可以在这里添加特定的数据预处理逻辑
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            预处理后的DataFrame
        """
        # 默认实现直接返回输入数据
        return df
    
    def after_signal_generation(self, signal: str, df: pd.DataFrame):
        """
        信号生成后的后处理
        
        可以在这里添加信号确认或风险控制逻辑
        
        Args:
            signal: 生成的信号
            df: K线数据DataFrame
        """
        # 默认实现为空
        pass 