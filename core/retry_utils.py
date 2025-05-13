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

import time
import functools
import logging

def retry(max_retries=3, base_delay=1.0, backoff=True):
    """
    重试装饰器，目的是为了应付突发的或者不稳定的网络导致的异常，增强程序的异常处理能力
    
    参数:
        max_retries (int): 最大重试次数
        base_delay (float): 初始重试延迟(秒)
        backoff (bool): 是否使用指数退避
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数名用于日志
            func_name = func.__name__
            
            # 获取logger - 假设是类方法且第一个参数是self
            logger = None
            if args and hasattr(args[0], 'logger'):
                logger = args[0].logger
            
            # 如果没有找到logger，使用默认的
            if not logger:
                logger = logging.getLogger('retry')
            
            # 重试逻辑
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # 如果是最后一次尝试，直接抛出异常
                    if attempt >= max_retries:
                        logger.error(f"{func_name} 在 {max_retries} 次尝试后失败: {str(e)}")
                        raise
                    
                    # 计算下次重试的等待时间
                    delay = base_delay
                    if backoff:
                        delay = base_delay * (2 ** (attempt - 1))
                    
                    logger.warning(f"{func_name} 尝试 {attempt}/{max_retries} 失败: {str(e)}. "
                                  f"等待 {delay:.2f}秒后重试...")
                    
                    # 等待后重试
                    time.sleep(delay)
            
            # 理论上不会执行到这里
            raise last_exception
        
        return wrapper
    return decorator 