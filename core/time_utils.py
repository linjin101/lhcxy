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

import datetime
import time
import re
import pytz

def get_seconds_from_timeframe(timeframe):
    """
    将时间周期字符串转换为秒数
    
    Args:
        timeframe: 时间周期字符串，如'1m', '15m', '30m', '1h', '4h', '1d'等
    
    Returns:
        int: 对应的秒数
    """
    # 使用正则表达式提取数字和单位
    match = re.match(r'(\d+)([mhdw])', timeframe.lower())
    if not match:
        raise ValueError(f"无效的时间周期格式: {timeframe}")
    
    value, unit = match.groups()
    value = int(value)
    
    # 转换为秒
    if unit == 'm':  # 分钟
        return value * 60
    elif unit == 'h':  # 小时
        return value * 60 * 60
    elif unit == 'd':  # 天
        return value * 24 * 60 * 60
    elif unit == 'w':  # 周
        return value * 7 * 24 * 60 * 60
    else:
        raise ValueError(f"不支持的时间单位: {unit}")

def get_local_timezone():
    """
    获取本地时区
    
    Returns:
        tzinfo: 本地时区对象
    """
    return datetime.datetime.now().astimezone().tzinfo

def utc_to_local(utc_dt):
    """
    将UTC时间转换为本地时间
    
    Args:
        utc_dt: UTC时间的datetime对象
    
    Returns:
        datetime: 本地时区的datetime对象
    """
    local_tz = get_local_timezone()
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=pytz.UTC)
    return utc_dt.astimezone(local_tz)

def calculate_next_candle_time(timeframe):
    """
    计算下一根K线的开始时间和需要等待的秒数
    
    Args:
        timeframe: 时间周期字符串，如'1m', '15m', '30m', '1h', '4h', '1d'等
    
    Returns:
        tuple: (下一根K线的开始时间(datetime), 需要等待的秒数(int))
    """
    # 获取当前UTC时间
    now = datetime.datetime.utcnow()
    seconds_per_candle = get_seconds_from_timeframe(timeframe)
    
    # 计算当前周期开始时间
    if timeframe.lower().endswith('m'):  # 分钟级别
        # 计算从一天开始已经过去了多少秒
        seconds_since_day_start = (
            now.hour * 3600 + 
            now.minute * 60 + 
            now.second
        )
        # 计算当前周期开始时间（向下取整到最近的一个周期起点）
        current_period_start_seconds = (seconds_since_day_start // seconds_per_candle) * seconds_per_candle
        current_period_start = now.replace(
            hour=current_period_start_seconds // 3600,
            minute=(current_period_start_seconds % 3600) // 60,
            second=0,
            microsecond=0
        )
        
    elif timeframe.lower().endswith('h'):  # 小时级别
        hours = int(timeframe[:-1])
        current_period_start = now.replace(
            hour=(now.hour // hours) * hours,
            minute=0,
            second=0,
            microsecond=0
        )
        
    elif timeframe.lower().endswith('d'):  # 天级别
        current_period_start = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
        
    else:  # 其他周期暂不详细处理，简单处理
        current_period_start = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
    
    # 计算下一个周期的开始时间
    next_period_start = current_period_start + datetime.timedelta(seconds=seconds_per_candle)
    
    # 如果计算出的下一周期开始时间已经过去，则再加一个周期
    while next_period_start <= now:
        next_period_start += datetime.timedelta(seconds=seconds_per_candle)
    
    # 计算需要等待的秒数
    wait_seconds = (next_period_start - now).total_seconds()
    
    return next_period_start, wait_seconds

def wait_for_next_candle(timeframe, buffer_seconds=5):
    """
    等待直到下一根K线形成后的buffer_seconds秒
    
    Args:
        timeframe: 时间周期字符串，如'1m', '15m', '30m', '1h', '4h', '1d'等
        buffer_seconds: 缓冲秒数，确保新K线数据已经可用
    
    Returns:
        datetime: 当前时间，表示可以开始执行策略
    """
    # 计算下一根K线时间和等待秒数
    next_candle_time, wait_seconds = calculate_next_candle_time(timeframe)
    
    # 打印等待信息
    now = datetime.datetime.utcnow()
    local_now = utc_to_local(now)
    local_next_candle_time = utc_to_local(next_candle_time)
    local_tz_name = local_now.tzinfo.tzname(local_now)
    
    print(f"当前时间: {local_now.strftime('%Y-%m-%d %H:%M:%S')} ({local_tz_name})")
    print(f"下一根{timeframe}K线时间: {local_next_candle_time.strftime('%Y-%m-%d %H:%M:%S')} ({local_tz_name})")
    print(f"等待{wait_seconds:.1f}秒后执行策略...")
    
    # 等待到下一根K线出现
    time.sleep(wait_seconds)
    
    # 额外等待buffer_seconds秒，确保新K线数据已经可用
    if buffer_seconds > 0:
        print(f"K线已形成，额外等待{buffer_seconds}秒确保数据可用...")
        time.sleep(buffer_seconds)
    
    # 返回当前时间
    return datetime.datetime.utcnow() 