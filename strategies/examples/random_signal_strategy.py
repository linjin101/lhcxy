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

import random
import pandas as pd
from core.strategy_template import StrategyTemplate
from core.signal_types import BUY, SELL, OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT, CLOSE_ALL

class RandomSignalStrategy(StrategyTemplate):
    """
    随机信号策略 - 生成随机交易信号，包括所有可能的信号类型，仅用于测试框架功能，不建议实盘使用
    """
    
    def __init__(self, trader, config):
        """
        初始化随机信号策略
        
        Args:
            trader: OkxTrader实例
            config: 策略配置
        """
        super().__init__(trader, config)
        self.signal_prob = config.get('signal_prob', 0.2)  # 产生信号的概率
        
        # 记录初始化信息
        self.logger.info(f"随机信号策略初始化，信号生成概率: {self.signal_prob}")
        
        # 定义所有可能的信号类型
        self.all_signals = [BUY, SELL, OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT, CLOSE_ALL]
        
        # 是否使用原始信号（仅BUY/SELL）
        self.use_legacy_signals_only = config.get('use_legacy_signals_only', False)
        
        # 是否只使用扩展信号（不包括BUY/SELL）
        self.use_extended_signals_only = config.get('use_extended_signals_only', False)
        
        # 根据配置确定使用的信号集合
        if self.use_legacy_signals_only:
            self.available_signals = [BUY, SELL]
            self.logger.info("仅使用原始信号: BUY, SELL")
        elif self.use_extended_signals_only:
            self.available_signals = [OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT, CLOSE_ALL]
            self.logger.info("仅使用扩展信号: OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT, CLOSE_ALL")
        else:
            self.available_signals = self.all_signals
            self.logger.info("使用所有信号类型")
    
    def on_initialize(self):
        """策略自定义初始化"""
        self.logger.info(f"随机信号策略准备就绪，将以{self.signal_prob}的概率生成随机交易信号")
        self.logger.info(f"可用信号: {', '.join(signal for signal in self.available_signals if signal is not None)}")
    
    def calculate_indicators(self, df):
        """
        计算技术指标 - 随机策略不需要指标
        
        Args:
            df: 包含K线数据的DataFrame
            
        Returns:
            DataFrame: 原始DataFrame
        """
        # 随机策略不需要计算指标，直接返回原始数据
        return df
    
    def generate_signals(self, df):
        """
        生成随机交易信号
        
        Args:
            df: 包含K线数据的DataFrame（仅用于记录信息，不参与信号生成）
            
        Returns:
            str: 随机交易信号
        """
        # 生成一个0-1之间的随机数
        r = random.random()
        self.logger.info(f'生成随机数: {r:.4f}, 信号阈值: {self.signal_prob:.4f}')
        
        # 获取当前持仓信息（用于智能随机）
        position = self.trader.fetch_position(self.symbol)
        current_position_side = None if position is None else position.get('side')
        
        # 根据设定的概率决定是否产生信号
        if r < self.signal_prob:
            # 基于当前持仓状态过滤不适合的信号
            appropriate_signals = self._filter_signals_by_position(current_position_side)
            
            if not appropriate_signals:
                self.logger.info("根据当前持仓状态，没有适合的信号可生成")
                return None
            
            # 随机选择一个适合的信号
            chosen_signal = random.choice(appropriate_signals)
            self.logger.info(f"随机生成信号: {chosen_signal}, 当前持仓状态: {current_position_side}")
            return chosen_signal
        else:
            # 无信号
            self.logger.info("本次没有生成交易信号")
            return None
    
    def _filter_signals_by_position(self, position_side):
        """
        根据当前持仓状态过滤出适合的信号
        
        Args:
            position_side: 当前持仓方向 ('long', 'short' 或 None)
            
        Returns:
            list: 适合当前持仓状态的信号列表
        """
        if position_side is None:
            # 无持仓时，只能开仓，不能平仓
            return [s for s in self.available_signals if s in [BUY, SELL, OPEN_LONG, OPEN_SHORT]]
        elif position_side == 'long':
            # 有多仓时，可以平多仓或平所有仓位，也可以开空仓（先平多再开空）
            return [s for s in self.available_signals if s in [SELL, CLOSE_LONG, CLOSE_ALL, OPEN_SHORT]]
        elif position_side == 'short':
            # 有空仓时，可以平空仓或平所有仓位，也可以开多仓（先平空再开多）
            return [s for s in self.available_signals if s in [BUY, CLOSE_SHORT, CLOSE_ALL, OPEN_LONG]]
        
        # 其他情况返回所有信号
        return self.available_signals 