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
import datetime
from core.data_feed import DataFeed
from core.position_manager import PositionManager
from core.logger_manager import logger_manager
from typing import Dict, Any, Optional, Tuple, List, Union
import time
from core.signal_types import *  # 导入信号类型常量
from core.position_tracker import PositionTracker  # 导入持仓跟踪器

# 导入通知管理器
from core.notification_manager import NotificationManager

class StrategyTemplate:
    """
    策略模板基类：为新手优化的策略开发模板
    
    此基类简化了策略开发流程，使用户只需关注核心的信号生成逻辑
    无需关心数据获取、交易执行等复杂底层细节
    
    注意：止盈止损功能已移至独立进程(tp_sl_monitor.py)，主策略进程不再处理止盈止损
    """
    
    def __init__(self, trader, config):
        """
        初始化策略模板
        
        Args:
            trader: OkxTrader实例
            config: 策略配置
        """
        self.trader = trader
        self.config = config
        self.symbol = config['symbol']
        self.timeframe = config.get('timeframe', '1h')
        
        # 初始化数据源
        self.data_feed = DataFeed(trader, self.symbol, self.timeframe)
        self.df = None
        
        # 获取日志记录器
        self.logger = logger_manager.get_strategy_logger()
        
        # 初始化仓位管理器
        self.position_manager = PositionManager(trader, config)
        
        # 获取持仓跟踪器 (仅用于持仓记录，不再用于止盈止损)
        self.position_tracker = PositionTracker.get_instance()
        # 设置trader引用，用于获取实时价格
        self.position_tracker.set_trader(trader)
        
        # 日志打印配置
        self.print_rows_limit = config.get('print_rows_limit', 15)  # 默认打印15条记录
        
        # 获取通知管理器
        try:
            self.notification_manager = NotificationManager.get_instance()
        except Exception as e:
            self.logger.warning(f"初始化通知管理器失败: {str(e)}，将禁用通知功能")
            self.notification_manager = None
        
        # 记录策略创建日志
        self.logger.info(f"策略初始化: {self.__class__.__name__}, 交易对: {self.symbol}, 时间周期: {self.timeframe}")
    
    def initialize(self):
        """
        策略初始化，获取初始数据并设置初始参数
        用户可以重写此方法来进行自定义初始化
        """
        self.logger.info(f"开始初始化策略: {self.__class__.__name__}")
        
        # 获取历史数据
        self.df = self.data_feed.update()
        
        # 记录初始化完成日志
        self.logger.info(f"策略 {self.__class__.__name__} 初始化完成，获取到 {len(self.df) if self.df is not None else 0} 条K线数据")
        logger_manager.log_system(
            "strategy_init", 
            f"策略 {self.__class__.__name__} 初始化完成，交易对: {self.symbol}",
            "info"
        )
        
        # 调用用户可重写的自定义初始化方法
        self.on_initialize()
    
    def on_initialize(self):
        """
        自定义初始化方法，用户可以重写此方法进行特定的初始化操作
        默认实现为空
        """
        pass
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        用户必须实现此方法，用于计算策略所需的各种技术指标
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            添加了技术指标的DataFrame
        """
        # 这是一个必须由子类实现的方法
        raise NotImplementedError("子类必须实现calculate_indicators方法来计算技术指标")
    
    def generate_signals(self, df: pd.DataFrame) -> str:
        """
        生成交易信号
        
        用户必须实现此方法，根据技术指标生成交易信号
        
        Args:
            df: 包含技术指标的K线数据DataFrame
            
        Returns:
            str: 交易信号，可用信号包括：
                - "BUY"/"OPEN_LONG": 买入/开多仓
                - "SELL"/"OPEN_SHORT": 卖出/开空仓
                - "CLOSE_LONG": 平多仓
                - "CLOSE_SHORT": 平空仓
                - "CLOSE_ALL": 平所有仓位
                - None: 无信号
        """
        # 这是一个必须由子类实现的方法
        raise NotImplementedError("子类必须实现generate_signals方法来生成交易信号")
    
    def on_bar(self, bar_data: pd.Series):
        """
        当新K线数据到来时调用，可用于实时数据更新处理
        用户可以重写此方法来处理每根新K线
        
        Args:
            bar_data: 最新K线数据
        """
        pass
    
    def before_signal_generation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        信号生成前的预处理，用户可重写此方法
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            预处理后的DataFrame
        """
        return df
    
    def after_signal_generation(self, signal: str, df: pd.DataFrame):
        """
        信号生成后的后处理，用户可重写此方法
        
        Args:
            signal: 生成的信号
            df: K线数据DataFrame
        """
        pass
    
    
    def _print_indicator_data(self, indicators_df):
        """
        打印指标数据，方便调试和观察
        
        Args:
            indicators_df: 包含技术指标的K线数据DataFrame
        """
        if indicators_df is None or indicators_df.empty:
            self.logger.warning("指标数据为空，无法打印")
            return
            
        self.logger.info(f"计算后的指标数据(最近{self.print_rows_limit}条):")
        indicator_tail = indicators_df.tail(self.print_rows_limit)
        
        # 获取所有列名
        columns = indicator_tail.columns.tolist()
        # 将时间和价格相关列放在前面显示
        key_columns = ['candle_begin_time_GMT8', 'open', 'high', 'low', 'close', 'volume']
        # 仅包含存在的key_columns
        key_columns = [col for col in key_columns if col in columns]
        # 添加其他自定义指标列(不包括已经在key_columns中的列)
        indicator_columns = [col for col in columns if col not in key_columns]
        display_columns = key_columns + indicator_columns[:10]  # 最多显示10个指标列避免日志过长
        
        # 打印表头和数据
        header_line = " | ".join([f"{col[:10]}" for col in display_columns])
        self.logger.info(f"指标列:{header_line}")
        
        # 打印具体数据行
        for _, row in indicator_tail.iterrows():
            data_line = " | ".join([f"{row[col]:.6f}" if isinstance(row[col], float) else f"{row[col]}" for col in display_columns])
            self.logger.info(f"数据行:{data_line}")

    
    def run(self) -> Tuple[Optional[str], Optional[pd.DataFrame]]:
        """
        运行策略的主方法，处理整个策略流程
        包括：获取数据、计算指标、生成信号、执行交易
        
        用户通常不需要修改此方法
        
        注意：止盈止损功能已移至独立进程(tp_sl_monitor.py)，主策略进程不再处理止盈止损
        
        Returns:
            tuple: (signal, df) 信号和处理后的数据
        """
        try:
            self.logger.info(f"开始运行策略: {self.__class__.__name__}")
            
            # 获取最新数据
            self.df = self.data_feed.update()
            if self.df is None or self.df.empty:
                self.logger.error("未能获取到有效K线数据")
                return None, None
            
            self.logger.info(f"获取到 {len(self.df)} 条K线数据")


            # 记录最新K线数据
            latest = self.df.tail(1).iloc[0]
            latest_price = latest['close']
            self.logger.info(f"最新K线: 时间={latest.get('candle_begin_time_GMT8', 'unknown')}, 价格={latest_price}")
            
            # 调用新K线处理方法
            self.on_bar(latest)
            
            # 获取当前持仓
            position = self.trader.fetch_position(self.symbol)
            
            # 更新持仓跟踪器 (仅用于记录持仓信息，不再处理止盈止损)
            self.position_tracker.update_position(self.symbol, position)
            
            # 注意：止盈止损检查功能已移至独立进程(tp_sl_monitor.py)
            
            # 预处理数据
            df_processed = self.before_signal_generation(self.df.copy())
            
            # 计算指标
            indicators_df = self.calculate_indicators(df_processed)
            
            # 打印指标数据，方便调试
            self._print_indicator_data(indicators_df)
            
            # 生成交易信号
            signal = self.generate_signals(indicators_df)
            
            # 信号生成后处理
            self.after_signal_generation(signal, indicators_df)
            
            # 执行交易
            if signal:
                self._execute_trade(signal, indicators_df)
            else:
                self.logger.info("没有生成交易信号")
            
            return signal, indicators_df
            
        except Exception as e:
            error_msg = f"策略执行出错: {str(e)}"
            self.logger.error(error_msg)
            import traceback
            self.logger.error(traceback.format_exc())
            
            # 使用静态方法发送错误通知
            NotificationManager.send_system_error(
                error_msg,
                f"{self.symbol} 策略执行错误",
                include_traceback=True
            )
            
            return None, None
    
    def _execute_trade(self, signal: Optional[str], df: pd.DataFrame) -> bool:
        """
        执行交易逻辑，处理各类交易信号并管理持仓
        
        此方法对用户隐藏，简化策略开发
        
        Args:
            signal: 交易信号，支持多种信号类型
            df: 市场数据DataFrame
            
        Returns:
            bool: 是否执行了交易
        """
        # 在方法开始时导入配置
        from config.config import position_config, symbol_position_config, notification_config
        
        # 验证信号有效性
        if not is_valid_signal(signal):
            self.logger.warning(f"未知交易信号: {signal}，忽略此信号")
            return False
            
        # 无交易信号
        if signal is None:
            self.logger.info(f"无交易信号，维持当前状态")
            return False
        
        # 获取当前持仓
        position = self.trader.fetch_position(self.symbol)
        
        # 获取最新价格和时间
        current_time = datetime.datetime.now()
        latest_price = df.iloc[-1]['close']
        
        # 检查是否使用动态仓位
        use_dynamic_position = self.config.get('use_dynamic_position', True)
        
        # 记录信号生成日志
        additional_info = {
            "price": latest_price,
            "strategy_config": str(self.config),
            "position": "无" if position is None else f"{position['side']} {position.get('contracts', 0)}"
        }
        logger_manager.log_signal(
            self.__class__.__name__, 
            self.symbol, 
            signal, 
            current_time,
            additional_info
        )
        
        # 处理向后兼容的信号转换
        action = get_signal_action(signal)
        
        # 处理开多仓信号
        if action == OPEN_LONG:
            # 如果有空仓先平仓
            if position and position['side'] == 'short':
                self.trader.close_short_position(self.symbol, float(position['contracts']))
                close_price = latest_price  # 使用当前价格作为平仓价格
                self.logger.info(f"平空仓完成，时间: {current_time}, 价格: {close_price}")
                
                # 获取平仓后的最新持仓状态
                # 稍微延迟以确保交易所数据已更新
                time.sleep(2)
                new_position = self.trader.fetch_position(self.symbol)
                
                # 更新持仓跟踪器
                self.position_tracker.update_position(self.symbol, new_position)
                
                # 使用新的综合通知方法
                if self.notification_manager:
                    if notification_config.get('notify_on_trade', True):
                        self.notification_manager.send_trade_notification(
                            strategy_name=self.__class__.__name__,
                            symbol=self.symbol,
                            action="平空仓",
                            amount=float(position['contracts']),
                            price=close_price,
                            position_info=new_position,
                            additional_info=f"策略产生开多信号，已执行平空仓操作"
                        )
            
            # 检查是否已有多仓
            if position and position['side'] == 'long':
                self.logger.info(f"已有多仓，无需开仓 - 时间: {current_time}, 价格: {latest_price}")
                return False
            
            # 确定仓位大小
            if use_dynamic_position:
                amount = self.position_manager.get_optimal_position_size(self.symbol, latest_price, 'buy')
                self.logger.info(f"使用动态仓位: {amount}")
            else:
                amount = self.config.get('amount', 1)
                self.logger.info(f"使用固定仓位: {amount}")
            
            # 确保仓位有效
            if amount <= 0:
                amount = self.config.get('amount', 1)
                self.logger.warning(f"仓位大小无效，使用默认值: {amount}")
            
            # 如果当前没有持仓，强制设置杠杆
            if position is None or position.get('contracts', 0) == 0:
                # 获取配置中的杠杆值
                leverage = self.config.get('leverage', 1)
                # 从position_config中获取杠杆优先级更高
                leverage = position_config.get('leverage', leverage)
                # 如果有交易对特定的杠杆设置，优先使用
                if self.symbol in symbol_position_config:
                    leverage = symbol_position_config[self.symbol].get('leverage', leverage)
                
                self.logger.info(f"当前无持仓，强制设置杠杆为: {leverage}倍")
                # 直接调用trader设置杠杆
                self.trader.set_leverage(self.symbol, leverage)
                # 记录杠杆设置
                self.logger.info(f"杠杆已强制设置，请确认交易所杠杆: {leverage}倍")
            
            # 执行买入操作
            order = self.trader.create_order(self.symbol, 'buy', amount)
            self.logger.info(f"执行买入: {amount} @ {latest_price}")
            
            # 获取开仓后的最新持仓状态
            # 稍微延迟以确保交易所数据已更新
            time.sleep(2)
            new_position = self.trader.fetch_position(self.symbol)
            
            # 更新持仓跟踪器
            self.position_tracker.update_position(self.symbol, new_position)
            
            # 使用新的综合通知方法
            if self.notification_manager:
                if notification_config.get('notify_on_trade', True):
                    order_id = order.get('id', '') if order else ''
                    self.notification_manager.send_trade_notification(
                        strategy_name=self.__class__.__name__,
                        symbol=self.symbol,
                        action="开多仓",
                        amount=amount,
                        price=latest_price,
                        position_info=new_position,
                        order_id=order_id,
                        additional_info=f"策略产生开多信号，已执行开多仓操作"
                    )
                
            return True
            
        # 处理开空仓信号
        elif action == OPEN_SHORT:
            # 如果有多仓先平仓
            if position and position['side'] == 'long':
                self.trader.close_long_position(self.symbol, float(position['contracts']))
                close_price = latest_price  # 使用当前价格作为平仓价格
                self.logger.info(f"平多仓完成，时间: {current_time}, 价格: {close_price}")
                
                # 获取平仓后的最新持仓状态
                # 稍微延迟以确保交易所数据已更新
                time.sleep(0.5)
                new_position = self.trader.fetch_position(self.symbol)
                
                # 更新持仓跟踪器
                self.position_tracker.update_position(self.symbol, new_position)
                
                # 使用新的综合通知方法
                if self.notification_manager:
                    if notification_config.get('notify_on_trade', True):
                        self.notification_manager.send_trade_notification(
                            strategy_name=self.__class__.__name__,
                            symbol=self.symbol,
                            action="平多仓",
                            amount=float(position['contracts']),
                            price=close_price,
                            position_info=new_position,
                            additional_info=f"策略产生开空信号，已执行平多仓操作"
                        )
            
            # 检查是否已有空仓
            if position and position['side'] == 'short':
                self.logger.info(f"已有空仓，无需开仓 - 时间: {current_time}, 价格: {latest_price}")
                return False
            
            # 确定仓位大小
            if use_dynamic_position:
                amount = self.position_manager.get_optimal_position_size(self.symbol, latest_price, 'sell')
                self.logger.info(f"使用动态仓位: {amount}")
            else:
                amount = self.config.get('amount', 1)
                self.logger.info(f"使用固定仓位: {amount}")
            
            # 确保仓位有效
            if amount <= 0:
                amount = self.config.get('amount', 1)
                self.logger.warning(f"仓位大小无效，使用默认值: {amount}")
            
            # 如果当前没有持仓，强制设置杠杆
            if position is None or position.get('contracts', 0) == 0:
                # 获取配置中的杠杆值
                leverage = self.config.get('leverage', 1)
                # 从position_config中获取杠杆优先级更高
                leverage = position_config.get('leverage', leverage)
                # 如果有交易对特定的杠杆设置，优先使用
                if self.symbol in symbol_position_config:
                    leverage = symbol_position_config[self.symbol].get('leverage', leverage)
                
                self.logger.info(f"当前无持仓，强制设置杠杆为: {leverage}倍")
                # 直接调用trader设置杠杆
                self.trader.set_leverage(self.symbol, leverage)
                # 记录杠杆设置
                self.logger.info(f"杠杆已强制设置，请确认交易所杠杆: {leverage}倍")
            
            # 执行卖出操作
            order = self.trader.create_order(self.symbol, 'sell', amount)
            self.logger.info(f"执行卖出: {amount} @ {latest_price}")
            
            # 获取开仓后的最新持仓状态
            # 稍微延迟以确保交易所数据已更新
            time.sleep(0.5)
            new_position = self.trader.fetch_position(self.symbol)
            
            # 更新持仓跟踪器
            self.position_tracker.update_position(self.symbol, new_position)
            
            # 使用新的综合通知方法
            if self.notification_manager:
                if notification_config.get('notify_on_trade', True):
                    order_id = order.get('id', '') if order else ''
                    self.notification_manager.send_trade_notification(
                        strategy_name=self.__class__.__name__,
                        symbol=self.symbol,
                        action="开空仓",
                        amount=amount,
                        price=latest_price,
                        position_info=new_position,
                        order_id=order_id,
                        additional_info=f"策略产生开空信号，已执行开空仓操作"
                    )
                
            return True
            
        # 处理平多仓信号
        elif action == CLOSE_LONG:
            # 检查是否有多仓
            if position and position['side'] == 'long':
                # 执行平多仓操作
                self.trader.close_long_position(self.symbol, float(position['contracts']))
                close_price = latest_price
                self.logger.info(f"平多仓完成，时间: {current_time}, 价格: {close_price}")
                
                # 获取平仓后的最新持仓状态
                time.sleep(0.5)
                new_position = self.trader.fetch_position(self.symbol)
                
                # 更新持仓跟踪器
                self.position_tracker.update_position(self.symbol, new_position)
                
                # 使用新的综合通知方法
                if self.notification_manager:
                    if notification_config.get('notify_on_trade', True):
                        self.notification_manager.send_trade_notification(
                            strategy_name=self.__class__.__name__,
                            symbol=self.symbol,
                            action="平多仓",
                            amount=float(position['contracts']),
                            price=close_price,
                            position_info=new_position,
                            additional_info=f"策略产生平多信号，已执行平多仓操作"
                        )
                return True
            else:
                self.logger.info(f"当前无多仓，无需平仓")
                return False
        
        # 处理平空仓信号
        elif action == CLOSE_SHORT:
            # 检查是否有空仓
            if position and position['side'] == 'short':
                # 执行平空仓操作
                self.trader.close_short_position(self.symbol, float(position['contracts']))
                close_price = latest_price
                self.logger.info(f"平空仓完成，时间: {current_time}, 价格: {close_price}")
                
                # 获取平仓后的最新持仓状态
                time.sleep(0.5)
                new_position = self.trader.fetch_position(self.symbol)
                
                # 更新持仓跟踪器
                self.position_tracker.update_position(self.symbol, new_position)
                
                # 使用新的综合通知方法
                if self.notification_manager:
                    if notification_config.get('notify_on_trade', True):
                        self.notification_manager.send_trade_notification(
                            strategy_name=self.__class__.__name__,
                            symbol=self.symbol,
                            action="平空仓",
                            amount=float(position['contracts']),
                            price=close_price,
                            position_info=new_position,
                            additional_info=f"策略产生平空信号，已执行平空仓操作"
                        )
                return True
            else:
                self.logger.info(f"当前无空仓，无需平仓")
                return False
                
        # 处理平所有仓位信号
        elif action == CLOSE_ALL:
            if position is None or position.get('contracts', 0) == 0:
                self.logger.info(f"当前无持仓，无需平仓")
                return False
                
            if position['side'] == 'long':
                # 平多仓
                self.trader.close_long_position(self.symbol, float(position['contracts']))
                close_price = latest_price
                self.logger.info(f"平多仓完成，时间: {current_time}, 价格: {close_price}")
                
                # 获取平仓后的最新持仓状态
                time.sleep(0.5)
                new_position = self.trader.fetch_position(self.symbol)
                
                # 更新持仓跟踪器
                self.position_tracker.update_position(self.symbol, new_position)
                
                # 使用新的综合通知方法
                if self.notification_manager:
                    if notification_config.get('notify_on_trade', True):
                        self.notification_manager.send_trade_notification(
                            strategy_name=self.__class__.__name__,
                            symbol=self.symbol,
                            action="平多仓",
                            amount=float(position['contracts']),
                            price=close_price,
                            position_info=None,
                            additional_info=f"策略产生平仓信号，已执行平多仓操作"
                        )
                return True
                
            elif position['side'] == 'short':
                # 平空仓
                self.trader.close_short_position(self.symbol, float(position['contracts']))
                close_price = latest_price
                self.logger.info(f"平空仓完成，时间: {current_time}, 价格: {close_price}")
                
                # 获取平仓后的最新持仓状态
                time.sleep(0.5)
                new_position = self.trader.fetch_position(self.symbol)
                
                # 更新持仓跟踪器
                self.position_tracker.update_position(self.symbol, new_position)
                
                # 使用新的综合通知方法
                if self.notification_manager:
                    if notification_config.get('notify_on_trade', True):
                        self.notification_manager.send_trade_notification(
                            strategy_name=self.__class__.__name__,
                            symbol=self.symbol,
                            action="平空仓",
                            amount=float(position['contracts']),
                            price=close_price,
                            position_info=None,
                            additional_info=f"策略产生平仓信号，已执行平空仓操作"
                        )
                return True
                
        # 未处理的信号类型
        self.logger.warning(f"未处理的信号类型: {signal}")
        return False 