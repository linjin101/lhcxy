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
交易信号类型定义

扩展的信号系统，提供更灵活的交易操作支持
"""

# 原始信号类型 - 向后兼容
BUY = "BUY"
SELL = "SELL"
NONE = None

# 扩展信号类型
OPEN_LONG = "OPEN_LONG"   # 开多仓
OPEN_SHORT = "OPEN_SHORT"  # 开空仓
CLOSE_LONG = "CLOSE_LONG"  # 平多仓
CLOSE_SHORT = "CLOSE_SHORT" # 平空仓
CLOSE_ALL = "CLOSE_ALL"    # 平所有仓位

# 信号类型分组
OPENING_SIGNALS = [BUY, SELL, OPEN_LONG, OPEN_SHORT]  # 开仓信号
CLOSING_SIGNALS = [CLOSE_LONG, CLOSE_SHORT, CLOSE_ALL]  # 平仓信号
ALL_VALID_SIGNALS = OPENING_SIGNALS + CLOSING_SIGNALS  # 所有有效信号

# 信号到操作的映射 - 用于向后兼容
SIGNAL_TO_ACTION = {
    BUY: OPEN_LONG,        # 原BUY信号映射到OPEN_LONG
    SELL: OPEN_SHORT,      # 原SELL信号映射到OPEN_SHORT
}

def is_valid_signal(signal):
    """
    检查信号是否有效
    
    Args:
        signal: 交易信号
        
    Returns:
        bool: 是否是有效的信号
    """
    if signal is None:
        return True  # None是有效的无操作信号
    return signal in ALL_VALID_SIGNALS

def get_signal_action(signal):
    """
    获取信号对应的动作，用于处理旧格式信号
    
    Args:
        signal: 原始信号
        
    Returns:
        对应的新格式信号动作
    """
    return SIGNAL_TO_ACTION.get(signal, signal)  # 如果没有映射关系，则返回原信号 