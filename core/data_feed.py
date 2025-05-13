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
from datetime import timedelta
from core.logger_manager import logger_manager

class DataFeed:
    def __init__(self, trader, symbol, timeframe, limit=1200):
        """
        初始化数据获取模块
        
        Args:
            trader: OkxTrader实例
            symbol: 交易对
            timeframe: 时间周期，如'1m', '5m', '1h', '1d'等
            limit: 获取K线的数量，默认1000条
        """
        self.trader = trader
        self.symbol = symbol
        self.timeframe = timeframe
        self.limit = limit
        self.data = []  # 存储原始K线数据
        self.df = None  # 存储处理后的DataFrame
        self.logger = logger_manager.get_system_logger()  # 获取系统日志记录器
        
    def update(self):
        """
        获取或更新K线数据

        Returns:
            pandas.DataFrame: K线数据
        """
        try:
            # 获取历史K线数据
            self.logger.info(f"获取K线数据 - {self.symbol} - {self.timeframe} - 数量: {self.limit}")
            ohlcv = self.trader.fetch_ohlcv(self.symbol, self.timeframe, self.limit)

            self.data = ohlcv  # 保存原始数据
            
            if ohlcv is None or len(ohlcv) == 0:
                self.logger.warning(f"获取到的K线数据为空 - {self.symbol} - {self.timeframe}")
                return pd.DataFrame()
            
            # 处理数据
            self._process_data()
            
            self.logger.info(f"成功获取了 {len(self.df)} 条K线数据")
            return self.df
            
        except Exception as e:
            error_msg = f"获取K线数据失败 - {self.symbol} - {self.timeframe}: {str(e)}"
            self.logger.error(error_msg)
            
            # 发送错误通知
            try:
                from core.notification_manager import NotificationManager
                notification_manager = NotificationManager.get_instance()
                if notification_manager:
                    from config.config import notification_config
                    if notification_config.get('notify_on_error', True):
                        notification_manager.send_error(
                            error_msg,
                            f"数据获取错误"
                        )
            except Exception as notify_error:
                self.logger.error(f"发送错误通知失败: {str(notify_error)}")
                
            return pd.DataFrame()
    
    def _process_data(self):
        """处理原始K线数据，转换为DataFrame格式"""
        if not self.data:
            self.df = pd.DataFrame()
            return
            
        # 创建DataFrame
        df = pd.DataFrame(self.data, dtype=float)
        
        # 重命名列
        df.rename(columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'}, inplace=True)
        
        # 转换时间戳为datetime格式
        df['candle_begin_time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # 转换为东八区时间(GMT+8)
        df['candle_begin_time_GMT8'] = df['candle_begin_time'] + timedelta(hours=8)
        
        # 选择需要的列并重新排序
        self.df = df[['candle_begin_time_GMT8', 'open', 'high', 'low', 'close', 'volume']]
        
        return self.df
        
    def get_latest_data(self, n=1):
        """
        获取最新N条DataFrame格式的数据
        
        Args:
            n: 需要获取的数据条数
            
        Returns:
            DataFrame: 最新的n条K线数据
        """
        if self.df is None or self.df.empty:
            return pd.DataFrame()
            
        if n <= len(self.df):
            return self.df.iloc[-n:]
        return self.df
    
    def get_raw_data(self):
        """
        获取原始K线数据
        
        Returns:
            list: 原始K线数据
        """
        return self.data 