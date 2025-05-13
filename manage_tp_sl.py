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


#!/usr/bin/env python3
"""
止盈止损监控进程管理工具

提供命令行界面，便于启动、停止和管理止盈止损监控进程
"""

import os
import sys
import time
import argparse
import subprocess
import json
from typing import List, Dict, Optional

def get_status() -> List[Dict]:
    """获取PM2进程状态"""
    try:
        result = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"获取PM2状态失败: {result.stderr}")
            return []
            
        return json.loads(result.stdout)
    except Exception as e:
        print(f"获取PM2状态时出错: {str(e)}")
        return []

def is_process_running(process_name: str) -> bool:
    """检查指定名称的进程是否正在运行"""
    processes = get_status()
    for proc in processes:
        if proc.get('name') == process_name and proc.get('pm2_env', {}).get('status') == 'online':
            return True
    return False

def start_processes(args):
    """启动进程"""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # 启动配置路径
    startup_json = os.path.join(current_dir, 'startup.json')
    
    if not os.path.exists(startup_json):
        print(f"错误: 找不到启动配置文件 {startup_json}")
        return
    
    if args.tp_sl_only:
        # 只启动止盈止损监控进程
        if is_process_running('tp-sl-monitor'):
            print("止盈止损监控进程已经在运行")
            return
            
        print("正在启动止盈止损监控进程...")
        result = subprocess.run(['pm2', 'start', startup_json, '--only', 'tp-sl-monitor'], 
                                capture_output=True, text=True)
    else:
        # 启动所有进程
        print("正在启动策略进程和止盈止损监控进程...")
        result = subprocess.run(['pm2', 'start', startup_json], 
                                capture_output=True, text=True)
    
    if result.returncode == 0:
        print("进程启动成功")
    else:
        print(f"进程启动失败: {result.stderr}")

def stop_processes(args):
    """停止进程"""
    if args.tp_sl_only:
        # 只停止止盈止损监控进程
        if not is_process_running('tp-sl-monitor'):
            print("止盈止损监控进程未运行")
            return
            
        print("正在停止止盈止损监控进程...")
        result = subprocess.run(['pm2', 'stop', 'tp-sl-monitor'], 
                                capture_output=True, text=True)
    else:
        # 停止所有进程
        print("正在停止策略进程和止盈止损监控进程...")
        result = subprocess.run(['pm2', 'stop', 'all'], 
                                capture_output=True, text=True)
    
    if result.returncode == 0:
        print("进程停止成功")
    else:
        print(f"进程停止失败: {result.stderr}")

def restart_processes(args):
    """重启进程"""
    if args.tp_sl_only:
        # 只重启止盈止损监控进程
        print("正在重启止盈止损监控进程...")
        result = subprocess.run(['pm2', 'restart', 'tp-sl-monitor'], 
                                capture_output=True, text=True)
    else:
        # 重启所有进程
        print("正在重启策略进程和止盈止损监控进程...")
        result = subprocess.run(['pm2', 'restart', 'all'], 
                                capture_output=True, text=True)
    
    if result.returncode == 0:
        print("进程重启成功")
    else:
        print(f"进程重启失败: {result.stderr}")

def show_logs(args):
    """显示日志"""
    if args.tp_sl_only:
        # 只显示止盈止损监控进程日志
        print("显示止盈止损监控进程日志...")
        os.system('pm2 logs tp-sl-monitor')
    else:
        # 显示所有进程日志
        print("显示所有进程日志...")
        os.system('pm2 logs')

def show_status(args):
    """显示进程状态"""
    # 运行PM2 list命令
    os.system('pm2 list')
    
    # 显示额外的止盈止损配置信息
    print("\n止盈止损配置信息:")
    try:
        from config.tp_sl_config import monitor_config, global_tp_sl_rules, symbol_tp_sl_rules
        
        print(f"检查间隔: {monitor_config.get('check_interval')}秒")
        print(f"监控交易对: {', '.join(monitor_config.get('symbols', []))}")
        
        for symbol in monitor_config.get('symbols', []):
            rules = symbol_tp_sl_rules.get(symbol, global_tp_sl_rules)
            tp_percentage = rules.get('take_profit_percentage', 0)
            sl_percentage = rules.get('stop_loss_percentage', 0)
            close_percentage = rules.get('close_percentage', 100)
            
            print(f"\n{symbol}配置:")
            print(f"  止盈: {tp_percentage}%")
            print(f"  止损: {sl_percentage}%")
            print(f"  平仓比例: {close_percentage}%")
    except Exception as e:
        print(f"获取配置信息失败: {str(e)}")

def run_test(args):
    """运行测试"""
    if args.unit:
        # 运行单元测试
        print("运行单元测试...")
        os.system('python test_tp_sl_monitor.py')
    else:
        # 运行手动测试
        print("运行手动测试...")
        os.system('python test_tp_sl_monitor.py --manual')

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description='止盈止损监控进程管理工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 启动命令
    start_parser = subparsers.add_parser('start', help='启动进程')
    start_parser.add_argument('--tp-sl-only', action='store_true', help='只启动止盈止损监控进程')
    start_parser.set_defaults(func=start_processes)
    
    # 停止命令
    stop_parser = subparsers.add_parser('stop', help='停止进程')
    stop_parser.add_argument('--tp-sl-only', action='store_true', help='只停止止盈止损监控进程')
    stop_parser.set_defaults(func=stop_processes)
    
    # 重启命令
    restart_parser = subparsers.add_parser('restart', help='重启进程')
    restart_parser.add_argument('--tp-sl-only', action='store_true', help='只重启止盈止损监控进程')
    restart_parser.set_defaults(func=restart_processes)
    
    # 日志命令
    logs_parser = subparsers.add_parser('logs', help='显示日志')
    logs_parser.add_argument('--tp-sl-only', action='store_true', help='只显示止盈止损监控进程日志')
    logs_parser.set_defaults(func=show_logs)
    
    # 状态命令
    status_parser = subparsers.add_parser('status', help='显示进程状态')
    status_parser.set_defaults(func=show_status)
    
    # 测试命令
    test_parser = subparsers.add_parser('test', help='运行测试')
    test_parser.add_argument('--unit', action='store_true', help='运行单元测试')
    test_parser.set_defaults(func=run_test)
    
    # 解析参数
    args = parser.parse_args()
    
    # 如果没有子命令，显示帮助
    if not hasattr(args, 'func'):
        parser.print_help()
        return
    
    # 执行相应的函数
    args.func(args)

if __name__ == "__main__":
    main() 