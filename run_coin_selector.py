"""
选币策略独立运行脚本

此脚本用于单独运行选币策略，获取推荐的交易币种列表
可以通过命令行参数控制是否持续运行

使用方法:
    python run_coin_selector.py           # 运行一次选币策略
    python run_coin_selector.py --loop    # 根据update_interval定时循环运行
"""

import sys
import time
import datetime
import importlib
from core.trader import OkxTrader
from core.time_utils import utc_to_local
from core.logger_manager import logger_manager
from config.config import trading_config, position_config, coin_selector_strategy_config
from config.api_keys import api_config


def run_coin_selector():
    """
    运行选币策略

    Args:
        loop_mode: 是否循环运行
    """
    # 获取当前本地时间
    now = datetime.datetime.now()
    local_time = now.astimezone()
    tz_name = local_time.tzinfo.tzname(local_time)

    # 设置日志
    logger = logger_manager.get_strategy_logger()

    # 打印启动信息
    logger.info("=" * 50)
    logger.info(f"OKX量化交易框架 - 选币策略独立运行")
    logger.info(f"启动时间: {local_time.strftime('%Y-%m-%d %H:%M:%S')} ({tz_name})")
    logger.info(f"选币时间周期: {coin_selector_strategy_config.get('timeframe', '4h')}")
    logger.info(f"选币模式: {coin_selector_strategy_config.get('selection_mode', 'trend')}")
    logger.info(f"选币数量: {coin_selector_strategy_config.get('num_coins', 5)}")
    logger.info(f"最小24h交易量(美元): {coin_selector_strategy_config.get('min_volume_usd', 10000000)}")

    # 获取调度配置
    schedule_hours = coin_selector_strategy_config.get('schedule_hours', [])
    if schedule_hours:
        logger.info(f"选币调度时间: 每天 {', '.join(map(str, schedule_hours))} 点")
    else:
        update_interval = coin_selector_strategy_config.get('update_interval', 24)
        logger.info(f"选币更新间隔: {update_interval}小时")

    logger.info(f"运行模式: {'循环模式' if coin_selector_strategy_config.get('loop_mode') else '单次运行'}")
    logger.info("=" * 50)

    try:
        # 初始化交易者
        trader = OkxTrader(
            api_config['api_key'],
            api_config['secret_key'],
            api_config['passphrase']
        )

        # 导入选币策略类
        try:
            from strategies.examples.coin_selector_strategy import CoinSelectorStrategy
        except ImportError:
            logger.error("导入选币策略失败，请确认策略文件存在")
            return

        # 合并配置
        config = {**trading_config, **coin_selector_strategy_config, **position_config}

        # 初始化选币策略
        strategy = CoinSelectorStrategy(trader, config)
        strategy.initialize()

        # 获取更新间隔（小时）
        update_interval = config.get('update_interval', 4)
        # 获取循环运行模式
        loop_mode = config.get('loop_mode', False)
        # 获取调度时间
        schedule_hours = config.get('schedule_hours', [])

        # 循环运行
        if loop_mode:

            # 循环运行模式
            if schedule_hours:
                logger.info(f"进入循环运行模式，每天 {', '.join(map(str, schedule_hours))} 点更新选币...")
            else:
                logger.info(f"进入循环运行模式，每{update_interval}小时更新一次选币...")

            try:
                # 首次运行
                strategy.run()

                while True:
                    # 计算下次运行时间
                    if schedule_hours:
                        # 使用固定时间调度
                        now = datetime.datetime.now()
                        current_hour = now.hour

                        # 找到今天下一个调度时间
                        next_hour = None
                        for hour in sorted(schedule_hours):
                            if hour > current_hour:
                                next_hour = hour
                                break

                        # 如果今天没有下一个调度时间，则使用明天的第一个调度时间
                        if next_hour is None:
                            next_hour = min(schedule_hours)
                            # 计算到明天该小时的秒数
                            next_run_time = datetime.datetime(now.year, now.month, now.day, next_hour, 0, 0)
                            next_run_time = next_run_time + datetime.timedelta(days=1)
                        else:
                            # 计算到今天该小时的秒数
                            next_run_time = datetime.datetime(now.year, now.month, now.day, next_hour, 0, 0)

                        # 计算等待时间（秒）
                        sleep_seconds = (next_run_time - now).total_seconds()
                        if sleep_seconds < 0:
                            sleep_seconds = 0

                        next_run_time_str = next_run_time.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        # 使用固定间隔调度
                        sleep_seconds = update_interval * 3600
                        next_run_time = datetime.datetime.now() + datetime.timedelta(seconds=sleep_seconds)
                        next_run_time_str = next_run_time.strftime('%Y-%m-%d %H:%M:%S')

                    logger.info(f"下次选币更新时间: {next_run_time_str}，等待中...")

                    # 每10分钟打印一次等待信息
                    for i in range(int(sleep_seconds / 600)):
                        time.sleep(600)  # 休眠10分钟
                        remaining = sleep_seconds - (i + 1) * 600
                        if remaining > 0:
                            hours = int(remaining / 3600)
                            minutes = int((remaining % 3600) / 60)
                            logger.info(f"距离下次选币更新还有: {hours}小时{minutes}分钟")

                    # 处理剩余的等待时间
                    remaining = sleep_seconds % 600
                    if remaining > 0:
                        time.sleep(remaining)

                    # 执行选币策略
                    strategy.run()

            except KeyboardInterrupt:
                logger.info("\n用户中断循环，程序结束")
        else:
            # 单次运行
            strategy.run()

    except KeyboardInterrupt:
        logger.info("\n用户中断，程序结束")
    except Exception as e:
        logger.error(f"程序发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    run_coin_selector()

