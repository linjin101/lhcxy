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

import logging
import os
from logging.handlers import TimedRotatingFileHandler
import datetime

class LoggerManager:
    """
    日志管理类，用于管理量化交易框架的日志记录
    支持将日志同时输出到控制台和文件，按日期自动切分日志文件
    """
    
    def __init__(self, log_dir="logs", log_level=logging.INFO):
        """
        初始化日志管理器
        
        Args:
            log_dir (str): 日志文件存储目录，默认为"logs"
            log_level (int): 日志级别，默认为INFO
        """
        self.log_dir = log_dir
        self.log_level = log_level
        self.loggers = {}
        
        # 确保日志目录存在
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def get_logger(self, name="main"):
        """
        获取指定名称的日志记录器
        
        Args:
            name (str): 日志记录器名称，默认为"main"
            
        Returns:
            logging.Logger: 日志记录器实例
        """
        # 如果已创建过该名称的日志记录器，直接返回
        if name in self.loggers:
            return self.loggers[name]
        
        # 创建新的日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # 如果已有处理器，则不重复添加
        if logger.handlers:
            return logger
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 创建文件处理器，按天切分
        log_file = os.path.join(self.log_dir, f"{name}.log")
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            interval=1,
            backupCount=30  # 保留30天的日志
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d.log"  # 日志文件后缀格式
        logger.addHandler(file_handler)
        
        # 存储日志记录器实例
        self.loggers[name] = logger
        return logger
    
    def get_trade_logger(self):
        """
        获取交易日志记录器
        
        Returns:
            logging.Logger: 交易日志记录器
        """
        return self.get_logger("trade")
    
    def get_strategy_logger(self):
        """
        获取策略日志记录器
        
        Returns:
            logging.Logger: 策略日志记录器
        """
        return self.get_logger("strategy")
    
    def get_system_logger(self):
        """
        获取系统日志记录器
        
        Returns:
            logging.Logger: 系统日志记录器
        """
        return self.get_logger("system")
    
    def get_market_logger(self):
        """
        获取市场数据日志记录器
        
        Returns:
            logging.Logger: 市场数据日志记录器
        """
        return self.get_logger("market")
    
    def get_position_logger(self):
        """
        获取仓位管理日志记录器
        
        Returns:
            logging.Logger: 仓位管理日志记录器
        """
        return self.get_logger("position")
    
    def get_test_logger(self):
        """
        获取测试日志记录器
        
        Returns:
            logging.Logger: 测试日志记录器
        """
        return self.get_logger("test")
    
    def log_trade(self, action, symbol, side, amount, price, order_id=None, additional_info=None):
        """
        记录交易日志
        
        Args:
            action (str): 交易操作，如"open", "close"
            symbol (str): 交易对
            side (str): 交易方向，如"buy", "sell"
            amount (float): 交易数量
            price (float): 交易价格
            order_id (str, optional): 订单ID
            additional_info (dict, optional): 附加信息
        """
        logger = self.get_trade_logger()
        
        # 构造日志消息
        msg = f"[TRADE] {action.upper()} - {symbol} - {side.upper()} - Amount: {amount} - Price: {price}"
        
        if order_id:
            msg += f" - OrderID: {order_id}"
        
        if additional_info:
            for key, value in additional_info.items():
                msg += f" - {key}: {value}"
        
        logger.info(msg)
    
    def log_signal(self, strategy_name, symbol, signal, timestamp=None, additional_info=None):
        """
        记录信号日志
        
        Args:
            strategy_name (str): 策略名称
            symbol (str): 交易对
            signal (str): 信号类型，如"BUY", "SELL", "NONE"
            timestamp (datetime, optional): 信号生成时间
            additional_info (dict, optional): 附加信息
        """
        logger = self.get_strategy_logger()
        
        if timestamp is None:
            timestamp = datetime.datetime.now()
        
        # 构造日志消息
        msg = f"[SIGNAL] {strategy_name} - {symbol} - {signal} - Time: {timestamp}"
        
        if additional_info:
            for key, value in additional_info.items():
                msg += f" - {key}: {value}"
        
        logger.info(msg)
    
    def log_system(self, event, message, level="info"):
        """
        记录系统日志
        
        Args:
            event (str): 事件类型
            message (str): 日志消息
            level (str): 日志级别，默认为"info"
        """
        logger = self.get_system_logger()
        
        # 构造日志消息
        msg = f"[SYSTEM] {event} - {message}"
        
        # 根据指定级别记录日志
        if level.lower() == "debug":
            logger.debug(msg)
        elif level.lower() == "warning":
            logger.warning(msg)
        elif level.lower() == "error":
            logger.error(msg)
        elif level.lower() == "critical":
            logger.critical(msg)
        else:
            logger.info(msg)
    
    def log_market(self, symbol, data_type, data_summary, timestamp=None):
        """
        记录市场数据日志
        
        Args:
            symbol (str): 交易对
            data_type (str): 数据类型，如"kline", "ticker"
            data_summary (str): 数据摘要
            timestamp (datetime, optional): 数据时间
        """
        logger = self.get_market_logger()
        
        if timestamp is None:
            timestamp = datetime.datetime.now()
        
        # 构造日志消息
        msg = f"[MARKET] {symbol} - {data_type} - {data_summary} - Time: {timestamp}"
        
        logger.info(msg)


# 创建全局日志管理器实例，便于在不同模块中使用相同的日志配置
logger_manager = LoggerManager() 