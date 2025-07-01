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

from core.trader import OkxTrader
from config.config import trading_config, position_config
from config.api_keys import api_config
import time
import datetime
import pytz
import importlib
import sys
import os
from core.time_utils import wait_for_next_candle, utc_to_local, calculate_next_candle_time
from core.logger_manager import logger_manager

# 策略配置字典，用于映射策略名称到配置和类
# -----------------------------------------------------------------------------------
# 重要说明：
# 本框架提供了一系列示例策略，位于strategies/examples/目录
# 包含详细的注释和教学内容，适合学习和修改
# 
# 在config.py中设置trading_config['strategy']时，使用下方映射表中的策略名称
# 例如: trading_config['strategy'] = 'bollinger_bands_strategy'
# -----------------------------------------------------------------------------------
STRATEGY_MAPPING = {
    # 策略名称: (模块路径, 类名, 配置变量名)
    'simple_ma_strategy': ('strategies.examples.simple_ma_strategy', 'SimpleMAStrategy', 'simple_ma_strategy_config'),
    'ema_strategy': ('strategies.examples.ema_strategy', 'EMAStrategy', 'ema_strategy_config'),
    'random_signal_strategy': ('strategies.examples.random_signal_strategy', 'RandomSignalStrategy', 'random_signal_strategy_config'),
    'sar_ema_strategy': ('strategies.examples.sar_ema_strategy', 'SarEmaStrategy', 'sar_ema_strategy_config'),
    'sar_emax_strategy': ('strategies.examples.sar_emax_strategy', 'SarEmaXStrategy', 'sar_emax_strategy_config'),
    'sar_strategy': ('strategies.examples.sar_strategy', 'SarStrategy', 'sar_strategy_config'),
    'dual_ema_strategy': ('strategies.examples.dual_ema_strategy', 'DualEMAStrategy', 'dual_ema_strategy_config'),
    'dc_strategy': ('strategies.examples.dc_strategy', 'DCStrategy', 'dc_strategy_config'),
    # 新增MA策略
    'dual_ma_strategy': ('strategies.examples.dual_ma_strategy', 'DualMAStrategy', 'dual_ma_strategy_config'),

}

def get_strategy_class(strategy_name):
    """
    根据策略名称动态导入并返回策略类和配置
    """
    if strategy_name not in STRATEGY_MAPPING:
        raise ValueError(f"未找到名为 '{strategy_name}' 的策略。可用的策略有: {', '.join(STRATEGY_MAPPING.keys())}")
    
    module_path, class_name, config_name = STRATEGY_MAPPING[strategy_name]
    
    try:
        # 动态导入策略模块
        strategy_module = importlib.import_module(module_path)
        # 获取策略类
        strategy_class = getattr(strategy_module, class_name)
        # 导入策略配置
        config_module = importlib.import_module('config.config')
        strategy_config = getattr(config_module, config_name)
        
        return strategy_class, strategy_config
    except ImportError as e:
        raise ImportError(f"导入策略 '{strategy_name}' 失败: {str(e)}。请确认策略文件位于 {module_path}.py")
    except AttributeError as e:
        raise AttributeError(f"加载策略 '{strategy_name}' 失败: {str(e)}。请确认策略类名为 {class_name}")

def run_strategy():
    """
    运行交易策略的主函数
    """
    # 获取选定的策略名称
    strategy_name = trading_config['strategy']
    timeframe = trading_config['timeframe']
    symbol = trading_config['symbol']
    
    # 获取当前本地时间
    now = datetime.datetime.now()
    local_time = now.astimezone()
    tz_name = local_time.tzinfo.tzname(local_time)
    
    # 设置日志
    logger = logger_manager.get_strategy_logger()
    
    # 打印启动信息
    logger.info("=" * 50)
    logger.info(f"OKX量化交易框架 - 启动")
    logger.info(f"策略: {strategy_name}")
    logger.info(f"启动时间: {local_time.strftime('%Y-%m-%d %H:%M:%S')} ({tz_name})")
    logger.info(f"交易对: {symbol}")
    logger.info(f"时间周期: {timeframe}")
    logger.info("交易模式: 实盘交易")
    logger.info("=" * 50)
    
    try:
        # 获取策略类和配置
        strategy_class, strategy_config = get_strategy_class(strategy_name)
        
        # 打印策略配置
        logger.info(f"策略配置:")
        for key, value in strategy_config.items():
            logger.info(f"  {key}: {value}")
        
        # 初始化交易者
        trader = OkxTrader(
            api_config['api_key'], 
            api_config['secret_key'], 
            api_config['passphrase']
        )

        # 判断仓位是否是双向持仓,如果不是会退出程序
        trader.check_position_is_dual_side()

        # 合并配置，确保包含仓位管理配置
        config = {**trading_config, **strategy_config, **position_config}
        logger.info(f"使用的杠杆配置: {position_config.get('leverage', 1)}倍")
        
        # 初始化策略
        strategy = strategy_class(trader, config)
        
        # 策略初始化
        strategy.initialize()
        
        logger.info(f"\n策略将按照{timeframe}周期同步执行")
        logger.info("策略将在每个新K线形成后立即执行")
        

        # 循环运行策略
        while True:
            try:
                # 添加下一次运行时间的日志
                next_candle_time, wait_seconds = calculate_next_candle_time(timeframe)
                local_next_candle_time = utc_to_local(next_candle_time)
                local_tz_name = local_next_candle_time.tzinfo.tzname(local_next_candle_time)
                logger.info(f"下一次运行时间: {local_next_candle_time.strftime('%Y-%m-%d %H:%M:%S')} ({local_tz_name}), 等待约 {wait_seconds:.1f} 秒")
                
                # 等待到下一根K线形成, 等30秒让交易所的k线数据产生
                wait_for_next_candle(timeframe, buffer_seconds=30)

                
                # 获取当前本地时间
                now = datetime.datetime.now().astimezone()
                tz_name = now.tzinfo.tzname(now)
                
                # 运行一次策略
                logger.info(f"\n运行策略 - {now.strftime('%Y-%m-%d %H:%M:%S')} ({tz_name})")
                signal, df = strategy.run()
                
                # 记录信号
                if signal:
                    logger.info(f"信号: {signal}")
                else:
                    logger.info("无交易信号")
                
                # 短暂休息，避免API请求过于频繁
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"策略运行出错: {str(e)}")
                logger.info("10秒后尝试重新运行...")
                time.sleep(10)
                
    except KeyboardInterrupt:
        logger.info("\n用户中断，程序结束")
    except Exception as e:
        logger.error(f"程序发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

def list_available_strategies():
    """显示所有可用的策略"""
    print("\n可用策略:")
    print("-" * 80)
    print(f"{'策略名称':<30} {'路径':<40} {'描述':<50}")
    print("-" * 80)
    
    for strategy_name, (module_path, class_name, _) in STRATEGY_MAPPING.items():
        try:
            # 尝试导入模块并获取描述
            strategy_module = importlib.import_module(module_path)
            strategy_class = getattr(strategy_module, class_name)
            description = getattr(strategy_class, '__doc__', '无描述').split('\n')[0].strip()
            print(f"{strategy_name:<30} {module_path:<40} {description:<50}")
        except (ImportError, AttributeError):
            print(f"{strategy_name:<30} {module_path:<40} {'(模块未找到)':<50}")
    
    print("-" * 80)
    print("\n使用方法: 在config/config.py中设置 trading_config['strategy'] = '策略名称'")
    print("示例: trading_config['strategy'] = 'bollinger_bands_strategy'")

if __name__ == "__main__":
    # 检查是否有命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        list_available_strategies()
    else:
        run_strategy() 