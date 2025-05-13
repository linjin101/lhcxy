#!/usr/bin/env python3

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

止盈止损监控器

该模块作为独立进程运行，负责监控持仓并执行止盈止损操作，
从而将止盈止损功能从策略主进程中分离出来，提高系统性能和稳定性。

"""

import time
import traceback
import logging
import os
import json
import datetime
from typing import Dict, List, Optional, Tuple

# 导入配置和工具模块
from config.config import position_config, symbol_position_config, notification_config, trading_config
from config.tp_sl_config import monitor_config, global_tp_sl_rules, position_report_config
from config.api_keys import api_config
from core.trader import OkxTrader
from core.position_tracker import PositionTracker
from core.logger_manager import logger_manager
from core.notification_manager import NotificationManager
from core.signal_types import *  # 导入所有信号类型

# 设置日志记录器
logger = logger_manager.get_logger("tp_sl_monitor")
trading_logger = logger_manager.get_trade_logger()

class TpSlMonitor:
    """
    止盈止损监控器
    
    监控所有交易对的持仓，检查是否达到止盈止损条件，
    并在达到条件时执行平仓操作。
    """
    
    def __init__(self):
        """初始化止盈止损监控器"""
        # 从api_config导入API密钥并初始化OkxTrader
        self.trader = OkxTrader(
            api_config['api_key'],
            api_config['secret_key'],
            api_config['passphrase']
        )
        
        # 获取持仓跟踪器实例
        self.position_tracker = PositionTracker.get_instance()
        
        # 设置持仓跟踪器的trader引用，用于获取实时价格
        self.position_tracker.set_trader(self.trader)
        
        self.notification = NotificationManager.get_instance()
        
        # 使用monitor_config中的监控间隔
        self.monitor_interval = monitor_config.get('check_interval', 5)
        self.logger = logger
        
        # 记录每个交易对最后一次触发止盈止损的时间
        self.last_tp_sl_times = {}
        # 从配置文件中获取止盈止损操作之间的冷却时间
        self.tp_sl_cooldown = monitor_config.get('tp_sl_cooldown', 300)  # 默认5分钟
        
        # 持仓报告相关配置
        self.position_report_enabled = position_report_config.get('enabled', False)
        self.position_report_interval = position_report_config.get('interval', 3600)  # 默认1小时
        self.position_report_detail = position_report_config.get('detail_level', 'normal')
        self.last_report_time = 0  # 上次发送报告的时间戳
        self.last_report_balance = 0  # 上次报告时的账户余额
        self.schedule_hours = position_report_config.get('schedule_hours', [])
        self.last_scheduled_hour = -1  # 上次定时发送的小时

        
        # 初始化
        self.logger.info(f"止盈止损监控器初始化完成，全局冷却时间设置为 {self.tp_sl_cooldown} 秒，监控间隔为 {self.monitor_interval} 秒")
        if self.position_report_enabled:
            if self.schedule_hours:
                hours_str = ", ".join([f"{h}:00" for h in self.schedule_hours])
                self.logger.info(f"定期持仓报告已启用，将在每天 {hours_str} 定时发送")
            else:
                self.logger.info(f"定期持仓报告已启用，间隔设置为 {self.position_report_interval} 秒")
    
    def get_position_config(self, symbol: str) -> Dict:
        """
        获取特定交易对的仓位配置
        
        Args:
            symbol: 交易对符号
            
        Returns:
            Dict: 仓位配置
        """
        # 首先使用全局止盈止损规则作为基础
        config = global_tp_sl_rules.copy()
        
        # 保证兼容性，也从position_config获取配置
        for key, value in position_config.items():
            if key not in config and key not in ['symbol_position_config']:
                config[key] = value
        
        # 最后检查是否有交易对特定配置
        if symbol in symbol_position_config:
            # 更新配置项
            for key, value in symbol_position_config[symbol].items():
                if key not in config:
                    config[key] = value
                
        return config
    
    def check_positions(self) -> None:
        """检查所有持仓的止盈止损条件"""
        try:
            # 获取所有交易对的持仓
            positions_list = self.trader.fetch_all_positions()
            
            if not positions_list:
                # 没有持仓，不需要检查
                self.logger.info("没有持仓，跳过止盈止损检查")
                return
            
            self.logger.info(f"获取到 {len(positions_list)} 个持仓")
            # 获取当前时间用于冷却检查
            current_time = time.time()
            
            # 处理返回的持仓列表
            for position in positions_list:
                # 跳过无效持仓
                if not position or not position.get('side') or float(position.get('contracts', 0)) <= 0:
                    continue
                
                # 获取交易对符号 - 优先使用info中的instId，这个是交易所原始格式
                # 如果没有，则回退到position的symbol
                symbol = None
                if 'info' in position and 'instId' in position['info']:
                    symbol = position['info']['instId']
                else:
                    symbol = position.get('symbol')
                
                if not symbol:
                    self.logger.warning(f"持仓数据中无法找到交易对符号: {position}")
                    continue
                
                # 获取交易对配置
                config = self.get_position_config(symbol)
                
                # 获取交易对特定的冷却时间配置
                tp_sl_cooldown = config.get('tp_sl_cooldown', self.tp_sl_cooldown)
                
                # 检查是否在冷却期内
                last_tp_sl_time = self.last_tp_sl_times.get(symbol, 0)
                if last_tp_sl_time > 0 and current_time - last_tp_sl_time < tp_sl_cooldown:
                    remaining_cooldown = int(tp_sl_cooldown - (current_time - last_tp_sl_time))
                    self.logger.info(f"{symbol} 在冷却期内，还剩 {remaining_cooldown} 秒")
                    continue
                
                # 获取持仓关键信息
                side = position.get('side', '')
                contracts = float(position.get('contracts', 0))
                entry_price = float(position.get('entryPrice', 0))
                current_price = float(position.get('markPrice', 0))
                leverage = float(position.get('leverage', 1))
                unrealized_pnl = float(position.get('unrealizedPnl', 0))
                
                # 计算盈亏百分比
                profit_percentage = 0
                if entry_price > 0 and current_price > 0:
                    if side == 'long':
                        profit_percentage = (current_price - entry_price) / entry_price * 100 * leverage
                    else:  # short
                        profit_percentage = (entry_price - current_price) / entry_price * 100 * leverage
                
                self.logger.info(f"检查持仓 {symbol} - {side} - {contracts} 的止盈止损条件")
                self.logger.info(f"{symbol} 开仓价: {entry_price}, 当前价: {current_price}, 盈亏: {profit_percentage:.2f}%, 杠杆: {leverage}倍")
                
                # 更新持仓记录 (仅用于记录历史数据)
                self.position_tracker.update_position(symbol, position)
                
                # 检查是否启用止盈止损
                if not config.get('enable_take_profit', False) and not config.get('enable_stop_loss', False):
                    self.logger.info(f"{symbol} 未启用止盈止损，跳过检查")
                    continue
                
                # 获取止盈止损设置
                tp_percentage = config.get('take_profit_percentage', 0)
                sl_percentage = config.get('stop_loss_percentage', 0)
                
                # 检查止盈条件
                if config.get('enable_take_profit', False) and tp_percentage > 0 and profit_percentage >= tp_percentage:
                    self.logger.info(f"{symbol} 触发止盈: 当前盈利 {profit_percentage:.2f}% >= 设定 {tp_percentage}%")
                    self._execute_tp_sl_trade(symbol, CLOSE_LONG if side == 'long' else CLOSE_SHORT, 
                                              current_price, position, config, profit_percentage, "止盈")
                    # 更新最后执行时间
                    self.last_tp_sl_times[symbol] = current_time
                
                # 检查止损条件
                elif config.get('enable_stop_loss', False) and sl_percentage > 0 and profit_percentage <= -sl_percentage:
                    self.logger.info(f"{symbol} 触发止损: 当前亏损 {-profit_percentage:.2f}% >= 设定 {sl_percentage}%")
                    self._execute_tp_sl_trade(symbol, CLOSE_LONG if side == 'long' else CLOSE_SHORT, 
                                             current_price, position, config, profit_percentage, "止损")
                    # 更新最后执行时间
                    self.last_tp_sl_times[symbol] = current_time
                else:
                    self.logger.info(f"{symbol} 未触发止盈止损: 当前盈亏 {profit_percentage:.2f}%, 止盈线 {tp_percentage}%, 止损线 {-sl_percentage}%")
                    
        except Exception as e:
            error_msg = f"检查止盈止损时发生错误: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            
            # 发送错误通知
            if notification_config.get('notify_on_error', True):
                self.notification.send_error(error_msg, "止盈止损系统错误")
    
    def _execute_tp_sl_trade(self, symbol: str, signal: str, price: float, position_data: Dict, config: Dict, profit_percentage: float, trigger_type: str) -> None:
        """
        执行止盈止损平仓操作
        
        Args:
            symbol: 交易对符号
            signal: 信号类型（CLOSE_LONG或CLOSE_SHORT）
            price: 触发价格
            position_data: 持仓数据
            config: 仓位配置
            profit_percentage: 盈亏百分比
            trigger_type: 触发类型（"止盈"或"止损"）
        """
        side = position_data.get('side')
        contracts = float(position_data.get('contracts', 0))
        entry_price = float(position_data.get('entryPrice', 0))
        leverage = float(position_data.get('leverage', 1))
        
        # 确保使用正确的交易对格式
        self.logger.info(f"开始执行{trigger_type}平仓，交易对: {symbol}，信号: {signal}，方向: {side}，杠杆: {leverage}倍，盈亏: {profit_percentage:.2f}%")
        
        # 记录冷却时间设置
        tp_sl_cooldown = config.get('tp_sl_cooldown', self.tp_sl_cooldown)
        self.logger.info(f"{symbol} 设置冷却时间 {tp_sl_cooldown} 秒，下次最早可触发时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + tp_sl_cooldown))}")
        
        self.logger.info(f"触发{symbol} {trigger_type}平仓: 信号={signal}, 当前价格={price}, 入场价={entry_price}")
        
        # 执行平仓交易
        try:
            result = None
            # 根据信号类型执行相应的平仓操作
            if signal == CLOSE_LONG and side == 'long':
                result = self.trader.close_long_position(symbol, contracts)
                action_status = "success" if result else "failed"
                result = {"status": action_status, "info": result}
            elif signal == CLOSE_SHORT and side == 'short':
                result = self.trader.close_short_position(symbol, contracts)
                action_status = "success" if result else "failed"
                result = {"status": action_status, "info": result}
            else:
                self.logger.warning(f"信号{signal}与持仓方向{side}不匹配，无法执行平仓")
                result = {"status": "failed", "reason": "signal_position_mismatch"}
            
            if result and result.get('status') == 'success':
                self.logger.info(f"{symbol} {trigger_type}平仓成功: {result}")
                
                # 发送通知
                if notification_config.get('notify_on_take_profit_stop_loss', True):
                    profit_str = f"盈利 {profit_percentage:.2f}%" if profit_percentage > 0 else f"亏损 {abs(profit_percentage):.2f}%"
                    
                    # 使用send_take_profit_stop_loss方法
                    if hasattr(self.notification, 'send_take_profit_stop_loss'):
                        self.notification.send_take_profit_stop_loss(
                            "止盈止损监控器",
                            symbol,
                            trigger_type,
                            '多头' if side == 'long' else '空头',
                            entry_price,
                            price,
                            contracts,
                            profit_percentage
                        )
                    else:
                        # 如果方法不存在，退回到send_text
                        message = f"{symbol} {trigger_type}平仓\n"
                        message += f"触发{trigger_type}条件，已平仓\n"
                        message += f"方向: {'多头' if side == 'long' else '空头'}\n"
                        message += f"数量: {contracts}\n"
                        message += f"入场价: {entry_price}\n"
                        message += f"平仓价: {price}\n"
                        message += f"杠杆: {leverage}倍\n"
                        message += f"结果: {profit_str}"
                        self.notification.send_text(message)
            else:
                self.logger.error(f"{symbol} {trigger_type}平仓失败: {result}")
                
        except Exception as e:
            error_msg = f"{symbol} {trigger_type}平仓执行错误: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            
            # 发送错误通知
            if notification_config.get('notify_on_error', True):
                self.notification.send_error(error_msg, f"{symbol} {trigger_type}平仓错误")
    
    def run(self) -> None:
        """启动止盈止损监控器"""
        self.logger.info("止盈止损监控器已启动，开始监控持仓...")
        
        try:
            while True:
                # 检查持仓的止盈止损条件
                self.check_positions()
                
                # 检查是否需要发送持仓报告
                if self.position_report_enabled:
                    self.check_and_send_position_report()
                
                # 等待下一次检查
                time.sleep(self.monitor_interval)
                
        except KeyboardInterrupt:
            self.logger.info("收到停止信号，止盈止损监控器正在停止...")
        except Exception as e:
            error_msg = f"止盈止损监控器运行错误: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            
            # 发送错误通知
            if notification_config.get('notify_on_error', True):
                self.notification.send_error(error_msg, "止盈止损系统崩溃")
            
            # 重新抛出异常
            raise
        finally:
            self.logger.info("止盈止损监控器已停止")

    def generate_position_report(self) -> Tuple[str, float]:
        """
        生成持仓报告
        
        根据配置的详细程度生成当前所有持仓的报告
        
        Returns:
            Tuple[str, float]: 报告内容和当前账户总余额
        """
        try:
            # 获取账户信息
            account_info = self.trader.get_account()
            total_balance = 0
            
            # 从OKX账户信息中提取USDT余额
            if account_info and 'data' in account_info and account_info['data']:
                balance_data = account_info['data'][0]
                if 'details' in balance_data and balance_data['details']:
                    details = balance_data['details'][0]
                    total_balance = float(details.get('cashBal', '0'))
            
            # 获取所有持仓
            positions_list = self.trader.fetch_all_positions()
            
            # 报告头部
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            account_alias = trading_config['account_alias']
            report = f"{account_alias}_持仓状态报告 - {now}\n\n"


            # 添加账户总览
            report += f"账户余额: {total_balance:.2f} USDT\n"
            
            # 如果没有持仓
            if not positions_list or len(positions_list) == 0:
                report += "\n当前无持仓\n"
                return report, total_balance
            
            # 计算持仓总价值
            total_position_value = 0
            for position in positions_list:
                if position and float(position.get('contracts', 0)) > 0:
                    notional = float(position.get('notional', 0))
                    total_position_value += abs(notional)
            
            report += f"持仓总价值: {total_position_value:.2f} USDT\n"
            report += f"持仓数量: {len(positions_list)}\n\n"
            
            # 持仓详情
            report += "===== 持仓详情 =====\n\n"
            
            # 遍历所有持仓
            for position in positions_list:
                # 跳过无效持仓
                if not position or not position.get('side') or float(position.get('contracts', 0)) <= 0:
                    continue
                
                # 获取交易对符号 - 优先使用info中的instId
                symbol = None
                if 'info' in position and 'instId' in position['info']:
                    symbol = position['info']['instId']
                else:
                    symbol = position.get('symbol')
                
                if not symbol:
                    continue
                
                # 获取持仓关键信息
                side = position.get('side', '')
                contracts = float(position.get('contracts', 0))
                entry_price = float(position.get('entryPrice', 0))
                current_price = float(position.get('markPrice', 0))
                leverage = float(position.get('leverage', 1))
                position_value = float(position.get('notional', 0))
                unrealized_pnl = float(position.get('unrealizedPnl', 0))
                
                # 计算盈亏百分比
                profit_percentage = 0
                if entry_price > 0 and current_price > 0:
                    if side == 'long':
                        profit_percentage = (current_price - entry_price) / entry_price * 100 * leverage
                    else:  # short
                        profit_percentage = (entry_price - current_price) / entry_price * 100 * leverage
                
                # 获取交易对配置
                config = self.get_position_config(symbol)

                # 获取合约k线周期
                timeframe = trading_config['timeframe']

                # 添加持仓信息到报告
                report += f"交易对: {symbol}\n"
                report += f"交易k线周期: {timeframe}\n"
                report += f"方向: {'多仓' if side == 'long' else '空仓'}\n"
                report += f"合约数量: {contracts}\n"
                report += f"开仓均价: {entry_price}\n"
                report += f"当前价格: {current_price}\n"
                report += f"杠杆倍数: {leverage}x\n"
                report += f"仓位价值: {abs(position_value):.2f} USDT\n"
                report += f"未实现盈亏: {unrealized_pnl:.2f} USDT ({profit_percentage:.2f}%)\n"
                
                # 如果是详细报告，添加更多信息
                if self.position_report_detail == 'detailed':
                    # 添加止盈止损配置
                    tp_percentage = config.get('take_profit_percentage', 0)
                    sl_percentage = config.get('stop_loss_percentage', 0)
                    report += f"止盈设置: {tp_percentage}%\n"
                    report += f"止损设置: {sl_percentage}%\n"
                    
                    # 计算止盈止损触发价格
                    if side == 'long':
                        tp_trigger = entry_price * (1 + tp_percentage / 100 / leverage)
                        sl_trigger = entry_price * (1 - sl_percentage / 100 / leverage)
                    else:  # short
                        tp_trigger = entry_price * (1 - tp_percentage / 100 / leverage)
                        sl_trigger = entry_price * (1 + sl_percentage / 100 / leverage)

                    report += f"止盈触发价: {tp_trigger:.4f}\n"
                    report += f"止损触发价: {sl_trigger:.4f}\n"
                    #
                    # # 添加持仓时间信息
                    # position_info = self.position_tracker.get_position_info(symbol)
                    # self.logger.info('!'*100)
                    # self.logger.info(position_info)
                    #
                    # if position_info and 'entry_time' in position_info:
                    #     entry_time = position_info['entry_time']
                    #     if isinstance(entry_time, datetime.datetime):
                    #         now = datetime.datetime.now()
                    #         duration = now - entry_time
                    #         hours = duration.total_seconds() / 3600
                    #         report += f"持仓时长: {hours:.1f}小时\n"
                
                report += "\n"
            
            return report, total_balance
        
        except Exception as e:
            error_msg = f"生成持仓报告时发生错误: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            return f"生成持仓报告失败: {str(e)}", 0
    
    def check_and_send_position_report(self) -> bool:
        """
        检查是否需要发送持仓报告，并在需要时发送
        
        Returns:
            bool: 是否成功发送报告
        """
        if not self.position_report_enabled:
            return False
        
        current_time = time.time()
        current_hour = datetime.datetime.now().hour
        
        # 检查是否为定时发送时间点
        scheduled_send = False
        if self.schedule_hours and current_hour in self.schedule_hours and current_hour != self.last_scheduled_hour:
            scheduled_send = True
            self.last_scheduled_hour = current_hour
        
        # 检查是否达到发送间隔
        interval_send = False
        if self.last_report_time == 0 or (current_time - self.last_report_time) >= self.position_report_interval:
            interval_send = True
        
        # 如果需要发送报告
        if scheduled_send or (interval_send and not self.schedule_hours):
            self.logger.info("准备发送定期持仓报告...")
            
            # 生成报告内容
            report_content, current_balance = self.generate_position_report()
            
            # 记录本次报告时间和余额
            self.last_report_time = current_time
            self.last_report_balance = current_balance
            
            # 发送报告
            success = self.notification.send_text(report_content)
            
            if success:
                self.logger.info("持仓报告发送成功")
            else:
                self.logger.error("持仓报告发送失败")
            
            return success
        
        return False


if __name__ == "__main__":
    """作为独立脚本运行时的入口点"""
    try:
        monitor = TpSlMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"止盈止损监控器启动失败: {str(e)}")
        logger.error(traceback.format_exc()) 