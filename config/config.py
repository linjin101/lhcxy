# config.py
"""
系统配置文件

包含交易策略、仓位管理和通知等相关配置
API密钥配置已移至api_keys.py文件
"""

# 交易配置（通用）
trading_config = {
    'account_alias':'量化机器人_1号', # 账户的昵称
    'symbol': 'WIF-USDT-SWAP',  # 交易对
    'strategy': 'dc_strategy',     # 策略名称
    'timeframe': '15m',         # K线时间周期
    'leverage': 1,              # 杠杆倍数
    'amount': 1,             # 固定仓位大小
    'use_dynamic_position': True,  # 是否使用动态仓位
    'is_test': False            # 测试模式，实盘如果设置True,仓位只会开30%资金
}


# 仓位管理配置
position_config = {
    'risk_percentage': 0.5,    # 每笔交易风险资金比例（账户资金的90%）
    'max_position_size': 1000000,    # 最大仓位大小（合约数量）
    'use_dynamic_sizing': True, # 是否使用动态仓位计算
    'leverage': 1,               # 默认杠杆倍数
}

dc_strategy_config ={
    'channel_period':20,
    'use_middle_exit':False, #这个参数不要改，目前只支持False
    'trade_direction':'both' # 交易方向，可选值: 'both', 'only_long', 'only_short'
}


# 交易对特定的仓位配置（覆盖全局配置）
symbol_position_config = {
}

# 策略特定配置 - 每个策略的特定参数

# 简单移动平均线策略参数 (simple_ma_strategy)
simple_ma_strategy_config = {
    'ma_period': 20,            # 移动平均线周期
    'ma_type': 'sma'            # 移动平均线类型 ('sma', 'ema', 'wma')
}


# EMA策略参数 (ema_strategy)
ema_strategy_config = {
    'ema_period': 21,           # EMA周期，默认21
}


# EMA策略参数 (ema_strategy)
dual_ema_strategy_config = {
    'fast_ema_period': 20,
    'slow_ema_period': 60,
    'trade_direction': 'only_short'  # 交易方向，可选值: 'both', 'only_long', 'only_short'
}

# sar+ema 策略
sar_ema_strategy_config = {
    'ema_period':200,
    'sar_acceleration':0.02,
    'sar_maximum':0.2
}

# sar策略
sar_strategy_config = {
    'sar_acceleration':0.02,
    'sar_maximum':0.2
}


# 随机信号策略参数 (用于测试，不建议实盘使用)
random_signal_strategy_config = {
    'signal_prob': 0.9,         # 随机信号生成概率(0-1之间)，越高生成信号的可能性越大
    'use_legacy_signals_only': False,  # 是否只使用传统信号(BUY/SELL)
    'use_extended_signals_only': False  # 是否只使用扩展信号(OPEN_LONG/OPEN_SHORT/CLOSE_LONG/CLOSE_SHORT/CLOSE_ALL)
    # 注意: 如果两个选项都为False，则使用所有信号类型
}

# 通知配置
notification_config = {
    # 是否启用通知
    'enabled': True,
    # 企业微信机器人webhook地址，通过企业微信群创建机器人获取
    'wechat_webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=3d63da38-94e5-4adc-b59c-e142c9ad91e3',
    
    # 通知事件设置
    'notify_on_error': True,        # 系统错误通知
    'notify_on_signal': False,      # 信号生成通知
    'notify_on_trade': True,        # 交易执行通知
    'notify_on_take_profit_stop_loss': True,  # 止盈止损触发通知
}

# 持仓报告配置
position_report_config = {
    'enabled': True,                # 是否启用定期持仓报告
    'interval': 120,               # 报告间隔时间（秒），3600=1小时，300=5分钟
    'detail_level': 'detailed',       # 报告详细程度：'brief'=简略, 'normal'=普通, 'detailed'=详细
    'schedule_hours': [],           # 指定每天的固定时间发送报告，空列表表示按interval发送,例如[9,12,15,18,21]表示这几个整点发送
    'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=3d63da38-94e5-4adc-b59c-e142c9ad91e3', # 持仓报告专用的webhook URL，为空则使用默认URL
}

# 选币策略配置
coin_selector_strategy_config = {
    'timeframe': '15m',  # 选币使用的K线周期
    'selection_mode': 'trend',  # 选币模式: trend(趋势), oscillation(震荡), comprehensive(综合)
    'num_coins': 5,  # 要选择的币种数量
    'min_volume_usd': 5000000,  # 最小24h交易量(美元)
    'update_interval': 1,  # 选币更新间隔(小时)
    'loop_mode': True,  # 是否循环运行选币策略
    'schedule_hours': [],  # 选币策略运行的固定时间点(小时),例如[9,12,15,18,21]表示这几个整点运行,空列表表示按update_interval间隔运行

    # 是否将选币结果输出到文件
    'output_to_file': True,
    # 输出文件路径，默认为logs目录下
    'output_file_path': 'logs/selected_coins.json',

    # 企业微信通知
    'enable_notifications': True,
    'wechat_webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=3d63da38-94e5-4adc-b59c-e142c9ad91e3',

    # 黑名单币种(不考虑的币种)
    'blacklist': [
        # 'LUNA-USDT-SWAP',
        # 'SHIT-USDT-SWAP',
        # 'PEOPLE-USDT-SWAP'
    ],

    # 白名单币种(只考虑这些币种，设置后会忽略黑名单)
    'whitelist': [],

    # 技术指标参数
    'fast_ema': 8,
    'slow_ema': 25,
    'volume_ma': 20,
    'rsi_period': 14,
    'atr_period': 14,

    # 选币权重配置
    'volume_weight': 0.2,  # 交易量权重
    'volatility_weight': 0.2,  # 波动性权重
    'trend_weight': 0.3,  # 趋势权重
    'momentum_weight': 0.2,  # 动量权重
    'correlation_weight': 0.1  # 相关性权重
}


# 帮助函数
def load_config():
    """加载配置，如果需要进行一些配置初始化工作可以在这里进行"""
    pass 
