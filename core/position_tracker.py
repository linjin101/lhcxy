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
持仓跟踪器

用于记录和跟踪持仓状态，包括入场价格、时间等信息，
并提供计算盈亏百分比等功能，支持止盈止损策略。
"""

import datetime
import json
import os
from typing import Dict, Optional, List, Tuple
from core.logger_manager import logger_manager

class PositionTracker:
    """
    持仓跟踪器类
    
    记录每个交易对的持仓状态，包括入场价格、时间等信息，
    计算盈亏百分比，并记录相关数据。
    
    注意：止盈止损功能已完全移至独立进程 tp_sl_monitor.py 处理，
    相关方法已从此类中移除。策略主进程不负责执行止盈止损检查和平仓操作。
    """
    
    _instance = None  # 单例模式
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = PositionTracker()
        return cls._instance
        
    def __init__(self):
        """初始化持仓跟踪器"""
        self.positions = {}  # 记录所有持仓信息
        self.history = []    # 历史交易记录
        self.logger = logger_manager.get_position_logger()
        self.trader = None   # 添加trader引用，初始为None
        
        # 加载历史记录
        self._load_history()
        
        self.logger.info("持仓跟踪器初始化完成")
    
    def set_trader(self, trader):
        """设置trader引用"""
        self.trader = trader
        self.logger.info("已设置trader引用")
    
    def update_position(self, symbol: str, position_data: Dict) -> None:
        """
        更新持仓信息
        
        Args:
            symbol: 交易对符号
            position_data: 持仓数据，包含side(方向)和contracts(数量)等信息
        """
        now = datetime.datetime.now()
        
        # 检查是否有持仓
        has_position = (position_data is not None and 
                      position_data.get('contracts', 0) > 0 and 
                      position_data.get('side') in ['long', 'short'])
        
        # 提取当前价格信息（如果可用）
        current_price = float(position_data.get('markPrice', 0)) if position_data else 0
        
        # 如果之前没有记录此交易对
        if symbol not in self.positions:
            if has_position:
                # 新建持仓记录
                self.positions[symbol] = {
                    'symbol': symbol,
                    'entryPrice': float(position_data.get('entryPrice', 0)),
                    'entry_time': now,
                    'side': position_data.get('side'),
                    'size': float(position_data.get('contracts', 0)),
                    'last_update_time': now,
                    'highest_price': float(position_data.get('entryPrice', 0)),
                    'lowest_price': float(position_data.get('entryPrice', 0)),
                    'last_price': current_price or float(position_data.get('entryPrice', 0)),
                    'leverage': float(position_data.get('leverage', 1))
                }

                self.logger.info(f'self.positions:{self.positions}')
                self.logger.info(f"新建{symbol}持仓记录 - 方向: {position_data.get('side')}, "
                               f"数量: {position_data.get('contracts')}, 价格: {position_data.get('entryPrice')}")
            else:
                # 无持仓，不需要记录
                return
        else:
            # 已有记录
            current_record = self.positions[symbol]
            
            # 更新最新价格
            if current_price > 0:
                current_record['last_price'] = current_price
            
            # 检查是否平仓或换方向
            if not has_position:
                # 平仓，记录历史并删除当前记录
                self._record_closed_position(symbol, current_price)
                self.logger.info(f"平仓 {symbol} - 原方向: {current_record['side']}, 原数量: {current_record['size']}")
                return
            
            # 检查是否换方向
            if current_record['side'] != position_data.get('side'):
                # 换方向，先记录平仓
                self._record_closed_position(symbol, current_price)
                # 然后创建新持仓
                self.positions[symbol] = {
                    'symbol': symbol,
                    'entryPrice': float(position_data.get('entryPrice', 0)),
                    'entry_time': now,
                    'side': position_data.get('side'),
                    'size': float(position_data.get('contracts', 0)),
                    'last_update_time': now,
                    'highest_price': float(position_data.get('entryPrice', 0)),
                    'lowest_price': float(position_data.get('entryPrice', 0)),
                    'last_price': current_price or float(position_data.get('entryPrice', 0)),
                    'leverage': float(position_data.get('leverage', 1))
                }
                self.logger.info(f'self.positions:{self.positions}')
                self.logger.info(f"换向 {symbol} - 新方向: {position_data.get('side')}, "
                               f"数量: {position_data.get('contracts')}, 价格: {position_data.get('entryPrice')}")
            else:
                # 相同方向，可能是加仓或减仓
                if float(position_data.get('contracts', 0)) != current_record['size']:
                    old_size = current_record['size']
                    new_size = float(position_data.get('contracts', 0))
                    
                    # 更新持仓量和平均入场价
                    current_record['size'] = new_size
                    # 当仓位变化时，交易所会自动计算新的平均入场价
                    current_record['entryPrice'] = float(position_data.get('entryPrice', current_record['entryPrice']))
                    current_record['last_update_time'] = now
                    
                    if new_size > old_size:
                        self.logger.info(f"加仓 {symbol} - 从 {old_size} 增加到 {new_size}, "
                                       f"新平均价格: {current_record['entryPrice']}")
                    else:
                        self.logger.info(f"减仓 {symbol} - 从 {old_size} 减少到 {new_size}, "
                                       f"新平均价格: {current_record['entryPrice']}")
    
    def update_market_price(self, symbol: str, current_price: float) -> None:
        """
        更新最新市场价格
        
        Args:
            symbol: 交易对符号
            current_price: 当前价格
        """
        if symbol not in self.positions:
            return
            
        record = self.positions[symbol]
        
        # 更新最高/最低价格和最新价格
        if current_price > record.get('highest_price', 0):
            record['highest_price'] = current_price
            
        if current_price < record.get('lowest_price', float('inf')) or record.get('lowest_price', 0) == 0:
            record['lowest_price'] = current_price
            
        # 更新最新价格
        record['last_price'] = current_price
    
    def calculate_profit_percentage(self, symbol: str, current_price: float) -> Optional[float]:
        """
        计算当前盈亏百分比
        
        Args:
            symbol: 交易对符号
            current_price: 当前价格
            
        Returns:
            float: 盈亏百分比，正数表示盈利，负数表示亏损，None表示无持仓
        """
        if symbol not in self.positions:
            return None
            
        record = self.positions[symbol]
        entryPrice = record['entryPrice']
        side = record['side']
        
        if entryPrice == 0:
            return None
            
        # 更新最新价格
        self.update_market_price(symbol, current_price)
        
        # 计算盈亏百分比
        if side == 'long':
            profit_pct = (current_price - entryPrice) / entryPrice * 100
        else:  # short
            profit_pct = (entryPrice - current_price) / entryPrice * 100
            
        # 考虑杠杆
        profit_pct = profit_pct * record.get('leverage', 1)
        
        return profit_pct
    
    def calculate_position_value(self, symbol: str, current_price: float) -> Optional[float]:
        """
        计算仓位当前价值
        
        Args:
            symbol: 交易对符号
            current_price: 当前价格
            
        Returns:
            float: 仓位价值，None表示无持仓
        """
        if symbol not in self.positions:
            return None
            
        record = self.positions[symbol]
        size = record['size']
        
        # 仓位价值 = 数量 * 当前价格
        position_value = size * current_price
        
        return position_value
    
    def get_position_info(self, symbol: str) -> Optional[Dict]:
        """
        获取持仓信息
        
        Args:
            symbol: 交易对符号
            
        Returns:
            Dict: 持仓信息，None表示无持仓
        """
        return self.positions.get(symbol)
    
    def _record_closed_position(self, symbol: str, exit_price: Optional[float]) -> None:
        """
        记录已平仓的持仓到历史记录
        
        Args:
            symbol: 交易对符号
            exit_price: 平仓价格，None表示尝试获取最新市场价格
        """
        if symbol not in self.positions:
            return
            
        record = self.positions[symbol].copy()
        record['exit_time'] = datetime.datetime.now()
        
        # 平仓价格处理逻辑改进
        if exit_price is not None and exit_price > 0:
            record['exit_price'] = exit_price
        else:
            # 首先尝试使用trader获取实时市场价格
            try:
                if self.trader is not None:
                    market_price = self.trader.fetch_market_price(symbol)
                    if market_price > 0:
                        record['exit_price'] = market_price
                        self.logger.info(f"使用trader获取的实时市场价格: {market_price}")
                    else:
                        raise ValueError("获取到的市场价格为0或负值")
                else:
                    raise ValueError("trader引用不可用")
            except Exception as e:
                self.logger.warning(f"无法获取实时市场价格: {str(e)}，尝试使用备选价格")
                
                # 尝试使用记录的最新价格
                if record.get('last_price', 0) > 0:
                    record['exit_price'] = record['last_price']
                    self.logger.info(f"使用记录的最新价格: {record['last_price']}")
                # 备选方案：根据持仓方向使用最高/最低价格
                elif record['side'] == 'long' and record.get('highest_price', 0) > 0:
                    # 多仓使用最高价格作为估计的平仓价格
                    record['exit_price'] = record['highest_price']
                    self.logger.info(f"使用记录的最高价格: {record['highest_price']}")
                elif record['side'] == 'short' and record.get('lowest_price', 0) > 0:
                    # 空仓使用最低价格作为估计的平仓价格
                    record['exit_price'] = record['lowest_price']
                    self.logger.info(f"使用记录的最低价格: {record['lowest_price']}")
                else:
                    # 最后的备选：使用入场价
                    record['exit_price'] = record.get('entryPrice', 0)
                    self.logger.info(f"使用入场价格: {record.get('entryPrice', 0)}")

        # 在日志中添加更多信息以帮助排查问题
        self.logger.info(f"处理平仓记录 - 使用的平仓价: {record.get('exit_price')}, "
                       f"原始传入价格: {exit_price}, "
                       f"入场价: {record['entryPrice']}")
        
        # 计算持仓时长
        if 'entry_time' in record and isinstance(record['entry_time'], datetime.datetime):
            duration = record['exit_time'] - record['entry_time']
            record['duration_hours'] = duration.total_seconds() / 3600
        
        # 计算盈亏百分比
        if record.get('exit_price') and record.get('entryPrice', 0) > 0:
            if record['side'] == 'long':
                record['profit_percentage'] = (record['exit_price'] - record['entryPrice']) / record['entryPrice'] * 100
            else:  # short
                record['profit_percentage'] = (record['entryPrice'] - record['exit_price']) / record['entryPrice'] * 100
            
            # 考虑杠杆
            record['profit_percentage'] = record['profit_percentage'] * record.get('leverage', 1)
        
        # 添加到历史记录
        self.history.append(record)
        
        # 创建一个易读的盈亏百分比字符串
        profit_str = f"{record.get('profit_percentage', 0):.2f}%" if 'profit_percentage' in record else 'unknown%'
        
        self.logger.info(f"记录{symbol}平仓历史 - 方向: {record['side']}, 数量: {record['size']}, "
                       f"入场价: {record['entryPrice']}, 平仓价: {record.get('exit_price', 'None')}, "
                       f"盈亏: {profit_str}")
        
        # 保存历史记录
        self._save_history()
        
        # 删除当前记录
        del self.positions[symbol]
    
    def _save_history(self) -> None:
        """保存交易历史到文件"""
        try:
            # 确保目录存在
            os.makedirs('data', exist_ok=True)
            
            # 转换datetime对象为字符串以便JSON序列化
            history_copy = []
            for record in self.history:
                record_copy = record.copy()
                if 'entry_time' in record_copy and isinstance(record_copy['entry_time'], datetime.datetime):
                    record_copy['entry_time'] = record_copy['entry_time'].isoformat()
                if 'exit_time' in record_copy and isinstance(record_copy['exit_time'], datetime.datetime):
                    record_copy['exit_time'] = record_copy['exit_time'].isoformat()
                if 'last_update_time' in record_copy and isinstance(record_copy['last_update_time'], datetime.datetime):
                    record_copy['last_update_time'] = record_copy['last_update_time'].isoformat()
                history_copy.append(record_copy)
            
            with open('data/trade_history.json', 'w') as f:
                json.dump(history_copy, f, indent=2)
        except Exception as e:
            self.logger.error(f"保存交易历史时发生错误: {str(e)}")
    
    def _load_history(self) -> None:
        """从文件加载交易历史"""
        try:
            if os.path.exists('data/trade_history.json'):
                with open('data/trade_history.json', 'r') as f:
                    history_data = json.load(f)
                
                # 转换字符串为datetime对象
                for record in history_data:
                    if 'entry_time' in record and isinstance(record['entry_time'], str):
                        record['entry_time'] = datetime.datetime.fromisoformat(record['entry_time'])
                    if 'exit_time' in record and isinstance(record['exit_time'], str):
                        record['exit_time'] = datetime.datetime.fromisoformat(record['exit_time'])
                    if 'last_update_time' in record and isinstance(record['last_update_time'], str):
                        record['last_update_time'] = datetime.datetime.fromisoformat(record['last_update_time'])
                
                self.history = history_data
                self.logger.info(f"加载了{len(self.history)}条交易历史记录")
        except Exception as e:
            self.logger.error(f"加载交易历史时发生错误: {str(e)}")
            # 发生错误时，创建空的历史记录
            self.history = [] 