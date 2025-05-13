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
通知管理器模块 - 提供企业微信等通知功能

用于在重要事件发生时（如信号生成、交易执行等）发送通知
"""

import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List, Union

class WeChatNotifier:
    """
    企业微信机器人通知类
    
    通过企业微信机器人webhook发送通知消息
    """
    
    def __init__(self, webhook_url: str, enabled: bool = True):
        """
        初始化微信通知器
        
        Args:
            webhook_url: 企业微信机器人的webhook地址
            enabled: 是否启用通知功能，默认为True
        """
        self.webhook_url = webhook_url
        self.enabled = enabled
        self.logger = logging.getLogger("notification")
        self.last_send_time = 0
        self.min_interval = 1  # 最小发送间隔，单位：秒
        
    def send_text(self, content: str) -> bool:
        """
        发送纯文本消息
        
        Args:
            content: 消息内容
            
        Returns:
            bool: 发送是否成功
        """
        if not self.enabled or not self.webhook_url:
            self.logger.warning("通知功能未启用或webhook URL未设置")
            return False
            
        # 检查发送频率
        current_time = time.time()
        if current_time - self.last_send_time < self.min_interval:
            time.sleep(self.min_interval - (current_time - self.last_send_time))
            
        # 构造消息
        message = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        # 发送请求
        try:
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(message),
                headers={'Content-Type': 'application/json'}
            )
            self.last_send_time = time.time()
            
            if response.status_code == 200:
                resp_data = response.json()
                if resp_data.get('errcode') == 0:
                    self.logger.info(f"通知发送成功: {content[:50]}...")
                    return True
                else:
                    self.logger.error(f"通知发送失败: {resp_data.get('errmsg')}")
            else:
                self.logger.error(f"通知HTTP请求失败，状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"发送通知时发生错误: {str(e)}")
            return False
    
    def send_markdown(self, content: str) -> bool:
        """
        发送markdown格式消息
        
        Args:
            content: markdown格式的消息内容
            
        Returns:
            bool: 发送是否成功
        """
        if not self.enabled or not self.webhook_url:
            self.logger.warning("通知功能未启用或webhook URL未设置")
            return False
            
        # 检查发送频率
        current_time = time.time()
        if current_time - self.last_send_time < self.min_interval:
            time.sleep(self.min_interval - (current_time - self.last_send_time))
            
        # 构造消息
        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        # 发送请求
        try:
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(message),
                headers={'Content-Type': 'application/json'}
            )
            self.last_send_time = time.time()
            
            if response.status_code == 200:
                resp_data = response.json()
                if resp_data.get('errcode') == 0:
                    self.logger.info(f"Markdown通知发送成功")
                    return True
                else:
                    self.logger.error(f"Markdown通知发送失败: {resp_data.get('errmsg')}")
            else:
                self.logger.error(f"通知HTTP请求失败，状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"发送Markdown通知时发生错误: {str(e)}")
            return False
    
    def send_trade_signal(self, strategy_name: str, symbol: str, signal: str, price: float, additional_info: str = "") -> bool:
        """
        发送交易信号通知
        
        Args:
            strategy_name: 策略名称
            symbol: 交易对
            signal: 信号类型（BUY/SELL）
            price: 价格
            additional_info: 附加信息
            
        Returns:
            bool: 发送是否成功
        """
        # 检查是否启用
        if not self.enabled:
            return False
            
        # 构造消息内容
        message = f"交易信号通知\n\n"
        message += f"策略: {strategy_name}\n"
        message += f"交易对: {symbol}\n"
        message += f"信号: {'买入' if signal == 'BUY' else '卖出'}\n"
        message += f"价格: {price}\n"
        
        if additional_info:
            message += f"信息: {additional_info}\n"
            
        message += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_text(message)
    
    def send_trade_execution(self, symbol: str, side: str, amount: float, price: float, order_id: str = "") -> bool:
        """
        发送交易执行通知
        
        Args:
            symbol: 交易对
            side: 交易方向（buy/sell）
            amount: 数量
            price: 价格
            order_id: 订单ID
            
        Returns:
            bool: 发送是否成功
        """
        # 构造消息内容
        message = f"交易执行通知\n\n"
        message += f"交易对: {symbol}\n"
        message += f"方向: {'买入' if side.lower() == 'buy' else '卖出'}\n"
        message += f"数量: {amount}\n"
        message += f"价格: {price}\n"
        
        if order_id:
            message += f"订单ID: {order_id}\n"
            
        message += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_text(message)
    
    def send_error(self, error_msg: str, error_type: str = "系统错误") -> bool:
        """
        发送错误通知
        
        Args:
            error_msg: 错误信息
            error_type: 错误类型
            
        Returns:
            bool: 发送是否成功
        """
        # 检查是否启用
        if not self.enabled:
            return False
            
        # 构造消息内容
        message = f"{error_type}\n\n"
        message += f"错误信息: {error_msg}\n"
        message += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_text(message)
    
    def send_take_profit_stop_loss(self, strategy_name: str, symbol: str, trigger_type: str, 
                               side: str, entry_price: float, exit_price: float, 
                               amount: float, profit_percentage: float) -> bool:
        """
        发送止盈止损触发通知
        
        Args:
            strategy_name: 策略名称
            symbol: 交易对
            trigger_type: 触发类型（take_profit/stop_loss）
            side: 持仓方向（long/short）
            entry_price: 入场价格
            exit_price: 出场价格
            amount: 平仓数量
            profit_percentage: 盈亏百分比
            
        Returns:
            bool: 发送是否成功
        """
        # 检查是否启用
        if not self.enabled:
            return False
            
        # 确定通知类型
        if trigger_type.lower() == 'take_profit' or trigger_type == '止盈':
            title = "止盈触发通知"
        else:  # stop_loss
            title = "止损触发通知"
            
        # 构造消息内容
        message = f"{title}\n\n"
        message += f"{trigger_type.upper()} 已触发\n\n"
        message += f"策略: {strategy_name}\n"
        message += f"交易对: {symbol}\n"
        message += f"持仓方向: {'多仓' if side.lower() == 'long' or side == '多头' else '空仓'}\n"
        message += f"入场价格: {entry_price}\n"
        message += f"出场价格: {exit_price}\n"
        message += f"平仓数量: {amount}\n"
        message += f"盈亏百分比: {profit_percentage:.2f}%\n"
        message += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_text(message)

class NotificationManager:
    """
    通知管理器类
    
    统一管理所有通知渠道，提供统一的通知接口
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            from config.config import notification_config
            cls._instance = cls(notification_config)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        
        # 初始化各通知渠道
        self.wechat = None
        
        # 创建企业微信通知器
        webhook_url = config.get('wechat_webhook_url', '')
        if webhook_url:
            self.wechat = WeChatNotifier(webhook_url, self.enabled)
            
        # 初始化日志
        self.logger = logging.getLogger("notification")
        self.logger.info("通知管理器初始化完成")
        
    def send_text(self, content: str) -> bool:
        """
        发送纯文本消息
        
        Args:
            content: 消息内容
            
        Returns:
            bool: 发送是否成功
        """
        if not self.enabled:
            return False
            
        success = False
        
        # 发送到企业微信
        if self.wechat:
            wechat_success = self.wechat.send_text(content)
            success = success or wechat_success
            
        return success
    
    def send_text_to_url(self, content: str, webhook_url: str) -> bool:
        """
        发送纯文本消息到指定的仓位 webhook URL
        
        Args:
            content: 消息内容
            webhook_url: 指定的webhook URL
            
        Returns:
            bool: 发送是否成功
        """

        if not webhook_url:
            self.logger.warning("webhook URL未提供，使用默认URL发送")
            return self.send_text(content)

        # 创建临时通知器发送消息
        temp_notifier = WeChatNotifier(webhook_url, enabled=True)
        success = temp_notifier.send_text(content)
        self.logger.info(f"使用指定仓位 webhook URL发送消息{'成功' if success else '失败'}")
        return success
    
    def send_trade_signal(self, strategy_name: str, symbol: str, signal: str, price: float, additional_info: str = "") -> bool:
        """
        发送交易信号通知
        
        Args:
            strategy_name: 策略名称
            symbol: 交易对
            signal: 信号类型（BUY/SELL）
            price: 价格
            additional_info: 附加信息
            
        Returns:
            bool: 发送是否成功
        """
        # 检查是否启用
        if not self.enabled:
            return False
            
        # 构造消息内容
        message = f"交易信号通知\n\n"
        message += f"策略: {strategy_name}\n"
        message += f"交易对: {symbol}\n"
        message += f"信号: {'买入' if signal == 'BUY' else '卖出'}\n"
        message += f"价格: {price}\n"
        
        if additional_info:
            message += f"信息: {additional_info}\n"
            
        message += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_text(message)
    
    def send_trade_notification(self, strategy_name: str, symbol: str, action: str, 
                                amount: float, price: float, position_info: dict = None, 
                                order_id: str = "", additional_info: str = "") -> bool:
        """
        发送综合交易通知（包含交易执行信息和仓位信息）
        
        Args:
            strategy_name: 策略名称
            symbol: 交易对
            action: 交易行为，如"开多"，"开空"，"平多"，"平空"
            amount: 交易数量
            price: 交易价格
            position_info: 仓位信息字典
            order_id: 订单ID
            additional_info: 附加信息
            
        Returns:
            bool: 发送是否成功
        """
        # 判断是否启用交易通知
        if not self.config.get('notify_on_trade', False):
            return False
            
        # 构造交易部分的消息
        message = f"交易执行通知 - {strategy_name}\n\n"
        message += f"交易操作: {action}\n"
        message += f"交易对: {symbol}\n"
        message += f"数量: {amount}\n"
        message += f"价格: {price}\n"
        
        if order_id:
            message += f"订单ID: {order_id}\n"
            
        if additional_info:
            message += f"说明: {additional_info}\n"
            
        message += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # 添加仓位信息（如果有）
        if position_info:
            message += "\n-----当前持仓信息-----\n"
            
            # 检查是否有仓位
            if position_info.get('side'):
                # 有仓位
                side = position_info.get('side', '')
                contracts = position_info.get('contracts', 0)
                entry_price = position_info.get('entryPrice', 0)
                mark_price = position_info.get('markPrice', 0)
                unrealized_pnl = position_info.get('unrealizedPnl', 0)
                leverage = position_info.get('leverage', 1)
                
                # 计算盈亏百分比
                if float(entry_price) > 0:
                    if side == 'long':
                        pnl_percent = (float(mark_price) - float(entry_price)) / float(entry_price) * 100
                    else:  # short
                        pnl_percent = (float(entry_price) - float(mark_price)) / float(entry_price) * 100
                else:
                    pnl_percent = 0
                
                # 格式化持仓信息
                message += f"持仓方向: {'多头' if side == 'long' else '空头'}\n"
                message += f"持仓数量: {contracts}\n"
                message += f"开仓均价: {entry_price}\n"
                message += f"当前价格: {mark_price}\n"
                
                # 格式化盈亏信息
                pnl_sign = "+" if float(unrealized_pnl) >= 0 else ""
                message += f"未实现盈亏: {pnl_sign}{unrealized_pnl} ({pnl_sign}{pnl_percent:.2f}%)\n"
                message += f"杠杆倍数: {leverage}x"
            else:
                # 无仓位
                message += "当前无持仓"
        
        # 发送到企业微信
        success = False
        if self.wechat:
            wechat_success = self.wechat.send_text(message)
            success = success or wechat_success
            
        return success
    
    def send_trade_execution(self, symbol: str, side: str, amount: float, price: float, order_id: str = "") -> bool:
        """
        发送交易执行通知
        
        Args:
            symbol: 交易对
            side: 交易方向（buy/sell）
            amount: 数量
            price: 价格
            order_id: 订单ID
            
        Returns:
            bool: 发送是否成功
        """
        if not self.enabled:
            return False
            
        success = False
        
        # 发送到企业微信
        if self.wechat:
            wechat_success = self.wechat.send_trade_execution(symbol, side, amount, price, order_id)
            success = success or wechat_success
            
        return success
    
    def send_error(self, error_msg: str, error_type: str = "系统错误") -> bool:
        """
        发送错误通知
        
        Args:
            error_msg: 错误信息
            error_type: 错误类型
            
        Returns:
            bool: 发送是否成功
        """
        # 检查是否启用
        if not self.enabled:
            return False
            
        # 构造消息内容
        message = f"{error_type}\n\n"
        message += f"错误信息: {error_msg}\n"
        message += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_text(message)
    
    def send_take_profit_stop_loss(self, strategy_name: str, symbol: str, trigger_type: str, 
                               side: str, entry_price: float, exit_price: float, 
                               amount: float, profit_percentage: float) -> bool:
        """
        发送止盈止损触发通知
        
        Args:
            strategy_name: 策略名称
            symbol: 交易对
            trigger_type: 触发类型（take_profit/stop_loss）
            side: 持仓方向（long/short）
            entry_price: 入场价格
            exit_price: 出场价格
            amount: 平仓数量
            profit_percentage: 盈亏百分比
            
        Returns:
            bool: 发送是否成功
        """
        if not self.enabled:
            self.logger.info("通知功能已禁用，不发送止盈止损通知")
            return False
            
        # 检查是否配置了发送止盈止损通知
        if not self.config.get('notify_on_take_profit_stop_loss', True):
            return False
            
        # 使用合适的通知渠道发送
        sent = False
        
        if self.wechat:
            sent = self.wechat.send_take_profit_stop_loss(
                strategy_name, symbol, trigger_type, side, 
                entry_price, exit_price, amount, profit_percentage
            )
            
        return sent
    
    @staticmethod
    def send_system_error(error_message: str, error_type: str = "系统错误", include_traceback: bool = True) -> bool:
        """
        发送系统错误通知的静态方法，可以被任何组件直接调用而无需先获取NotificationManager实例
        
        Args:
            error_message: 错误消息内容
            error_type: 错误类型，默认为"系统错误"
            include_traceback: 是否包含堆栈跟踪信息
            
        Returns:
            bool: 是否成功发送通知
        """
        try:
            # 导入需要的模块
            from core.logger_manager import logger_manager
            from config.config import notification_config
            
            # 获取日志记录器
            logger = logger_manager.get_logger("notification")
            
            # 检查通知配置
            if not notification_config.get('notify_on_error', True):
                logger.info("错误通知功能已禁用，跳过发送")
                return False
                
            # 获取堆栈跟踪信息
            traceback_info = ""
            if include_traceback:
                import traceback
                traceback_info = f"\n\n堆栈跟踪：\n{traceback.format_exc()[:800]}..."
                
            # 获取通知管理器实例并发送错误
            notifier = NotificationManager.get_instance()
            result = notifier.send_error(f"{error_message}{traceback_info}", error_type)
            
            if result:
                logger.info(f"已发送错误通知: {error_type}")
            else:
                logger.warning(f"发送错误通知失败: {error_type}")
                
            return result
            
        except Exception as e:
            # 出现异常时尝试记录日志，但不要再抛出异常
            try:
                from core.logger_manager import logger_manager
                logger = logger_manager.get_logger("notification")
                logger.error(f"发送系统错误通知时遇到异常: {str(e)}")
            except:
                pass  # 如果连日志也无法记录，则静默失败
            return False 