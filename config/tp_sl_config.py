# tp_sl_config.py
"""
止盈止损监控进程配置文件

包含监控频率、止盈止损规则和错误处理等相关配置
"""

# 监控进程基本配置
monitor_config = {
    'check_interval': 30,       # 监控价格检查间隔（秒）
    'max_retries': 5,           # 最大重试次数
    'retry_delay': 3,         # 初始重试延迟（秒）
    'log_level': 'INFO',        # 日志级别
    'symbols': ['auto'],        # 'auto'表示自动检测要监控的交易对
    'tp_sl_cooldown': 3600      # 止盈止损操作之间的冷却时间（秒）
}


# 止盈止损规则配置
# 全局默认规则，适用于所有交易对
global_tp_sl_rules = {
    'enable_take_profit': True,   # 是否启用止盈
    'enable_stop_loss': True,     # 是否启用止损
    'take_profit_percentage': 10.0,  # 止盈百分比
    'stop_loss_percentage': 10.0,    # 止损百分比
    'close_percentage': 100,        # 触发时平仓百分比 (100表示全部平仓)
}


# 持仓报告配置
position_report_config = {
    'enabled': True,                # 是否启用定期持仓报告
    'interval': 120,               # 报告间隔时间（秒），3600=1小时，300=5分钟
    'detail_level': 'detailed',       # 报告详细程度：'brief'=简略, 'normal'=普通, 'detailed'=详细
    'include_small_positions': True, # 是否包含小额持仓（相对于总资产）
    'schedule_hours': [],           # 指定每天的固定时间发送报告，空列表表示按interval发送,例如[9,12,15,18,21]表示这几个整点发送
}


# 通知设置
notification_settings = {
    'enable_notifications': True,          # 是否启用通知
    'notify_on_tp_sl_triggered': True,     # 止盈止损触发时通知
    'notify_on_error': True,               # 错误发生时通知
    'notify_on_restart': True,             # 进程重启时通知
}
