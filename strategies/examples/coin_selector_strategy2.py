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
智能选币策略

这是一个基于多维度指标的选币策略：
- 分析交易量、波动性、趋势强度等多个维度
- 支持多种选币模式：趋势型、震荡型、综合型
- 可以根据不同的市场环境自动调整选币标准
"""

from core.strategy_template import StrategyTemplate
from core.signal_types import BUY, SELL, OPEN_LONG, OPEN_SHORT
import pandas as pd
import numpy as np
import time
import os
import json
import datetime


class CoinSelectorStrategy2(StrategyTemplate):
    """
    智能选币策略

    通过分析多个维度的指标，从交易所可交易的币种中筛选出最具潜力的币种：
    - 流动性分析：交易量、买卖盘深度
    - 波动性分析：ATR、价格波动率
    - 趋势分析：均线系统、趋势强度
    - 动量分析：RSI、MACD等指标
    - 相关性分析：与大盘的相关性

    支持多种选币模式，适应不同的市场环境和交易策略
    """

    def __init__(self, trader, config):
        """
        初始化选币策略

        Args:
            trader: OkxTrader实例
            config: 策略配置
        """
        super().__init__(trader, config)

        # 获取基本配置
        self.timeframe = config.get('timeframe', '4h')
        self.selection_mode = config.get('selection_mode', 'comprehensive')  # 可选: trend, oscillation, comprehensive
        self.num_coins = config.get('num_coins', 5)  # 要选择的币种数量
        self.min_volume_usd = config.get('min_volume_usd', 1000000)  # 最小24h交易量(美元)
        self.update_interval = config.get('update_interval', 24)  # 选币更新间隔(小时)
        self.blacklist = config.get('blacklist', [])  # 黑名单币种
        self.whitelist = config.get('whitelist', [])  # 白名单币种

        # 文件输出配置
        self.output_to_file = config.get('output_to_file', False)  # 是否输出到文件
        self.output_file_path = config.get('output_file_path', 'logs/selected_coins.json')  # 输出文件路径

        # 发送企业微信通知
        self.enable_notifications = self.config.get('enable_notifications', False)  # 是否启用企业微信通知
        self.wechat_webhook_url = self.config.get('wechat_webhook_url', '')  # 企业微信Webhook URL

        # 技术指标参数
        self.fast_ema = config.get('fast_ema', 20)
        self.slow_ema = config.get('slow_ema', 55)
        self.volume_ma = config.get('volume_ma', 20)
        self.rsi_period = config.get('rsi_period', 14)
        self.atr_period = config.get('atr_period', 14)

        # 选币权重配置
        self.weights = {
            'volume': config.get('volume_weight', 0.2),
            'volatility': config.get('volatility_weight', 0.2),
            'trend': config.get('trend_weight', 0.3),
            'momentum': config.get('momentum_weight', 0.2),
            'correlation': config.get('correlation_weight', 0.1)
        }

        # 根据选币模式调整权重
        if self.selection_mode == 'trend':
            self.weights['trend'] = 0.5
            self.weights['momentum'] = 0.3
            self.weights['volatility'] = 0.1
            self.weights['volume'] = 0.1
            self.weights['correlation'] = 0.0
        elif self.selection_mode == 'oscillation':
            self.weights['volatility'] = 0.4
            self.weights['momentum'] = 0.3
            self.weights['volume'] = 0.2
            self.weights['trend'] = 0.0
            self.weights['correlation'] = 0.1

        # 初始化选币结果和上次更新时间
        self.selected_coins = []
        self.last_update_time = 0

        # 记录策略信息
        self.logger.info(f"初始化智能选币策略，模式: {self.selection_mode}, "
                         f"选币数量: {self.num_coins}, 时间周期: {self.timeframe}")
        self.logger.info(f"选币权重: 交易量({self.weights['volume']}), "
                         f"波动性({self.weights['volatility']}), "
                         f"趋势({self.weights['trend']}), "
                         f"动量({self.weights['momentum']}), "
                         f"相关性({self.weights['correlation']})")

        if self.output_to_file:
            self.logger.info(f"选币结果将输出到文件: {self.output_file_path}")

    def initialize(self):
        """
        策略初始化，执行首次选币
        """
        self.logger.info("开始初始化选币策略...")
        self.selected_coins = self.select_coins()
        self.last_update_time = time.time()
        self.logger.info(f"初始选币完成，选中: {self.selected_coins}")

        # 如果配置了输出到文件，则将结果写入文件
        if self.output_to_file and self.selected_coins:
            self.output_selected_coins_to_file()

    def run(self):
        """
        运行策略，定期更新选币结果

        Returns:
            None, 选币策略不生成交易信号
        """
        current_time = time.time()
        current_datetime = datetime.datetime.fromtimestamp(current_time)
        hours_since_update = (current_time - self.last_update_time) / 3600

        # 获取调度时间配置
        schedule_hours = self.config.get('schedule_hours', [])

        # 判断是否需要更新选币
        need_update = False

        if schedule_hours:
            # 使用固定时间调度
            current_hour = current_datetime.hour
            # 检查当前小时是否在调度时间列表中
            if current_hour in schedule_hours:
                # 检查在这个小时内是否已经更新过
                last_update_hour = datetime.datetime.fromtimestamp(self.last_update_time).hour
                last_update_day = datetime.datetime.fromtimestamp(self.last_update_time).day
                current_day = current_datetime.day

                # 如果是同一天同一小时，则不更新；如果是不同天或不同小时，则更新
                if not (current_day == last_update_day and current_hour == last_update_hour):
                    need_update = True
                    self.logger.info(f"当前时间 {current_hour}:00 在调度时间列表中，开始更新选币...")
        else:
            # 使用固定间隔调度
            if hours_since_update >= self.update_interval:
                need_update = True
                self.logger.info(f"距离上次选币已过{hours_since_update:.1f}小时，开始更新选币...")

        # 执行选币更新
        if need_update:
            self.selected_coins = self.select_coins()
            self.last_update_time = current_time
            self.logger.info(f"选币更新完成，新选中: {self.selected_coins}")

            # 如果配置了输出到文件，则将结果写入文件
            if self.output_to_file and self.selected_coins:
                self.output_selected_coins_to_file()
        else:
            if schedule_hours:
                # 计算下一个调度时间
                next_hour = None
                for hour in sorted(schedule_hours):
                    if hour > current_datetime.hour:
                        next_hour = hour
                        break

                if next_hour is None:
                    next_hour = min(schedule_hours)
                    self.logger.info(f"今日选币已完成，下次选币时间为明天 {next_hour}:00")
                else:
                    self.logger.info(f"当前不在调度时间，下次选币时间为今天 {next_hour}:00")
            else:
                self.logger.info(f"距离上次选币{hours_since_update:.1f}小时，未达到更新间隔{self.update_interval}小时")

        # 选币策略不生成交易信号
        return None, None

    def output_selected_coins_to_file(self):
        """
        将选币结果输出到文件
        """
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(self.output_file_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 准备输出数据
            update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_update_time))
            output_data = {
                'timestamp': update_time,
                'timeframe': self.timeframe,
                'selection_mode': self.selection_mode,
                'selected_coins': self.selected_coins
            }

            # 写入文件
            with open(self.output_file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4, ensure_ascii=False)

            self.logger.info(f"选币结果已成功输出到文件: {self.output_file_path}")

            if self.enable_notifications and self.wechat_webhook_url and self.selected_coins:
                try:
                    from core.notification_manager import WeChatNotifier

                    notifier = WeChatNotifier(self.wechat_webhook_url, True)

                    # 计算下次更新时间
                    next_update_time = ""
                    schedule_hours = self.config.get('schedule_hours', [])
                    current_time = time.time()
                    current_datetime = datetime.datetime.fromtimestamp(current_time)

                    if schedule_hours:
                        # 使用固定时间调度
                        current_hour = current_datetime.hour

                        # 找到今天下一个调度时间
                        next_hour = None
                        for hour in sorted(schedule_hours):
                            if hour > current_hour:
                                next_hour = hour
                                break

                        # 如果今天没有下一个调度时间，则使用明天的第一个调度时间
                        if next_hour is None:
                            next_hour = min(schedule_hours)
                            next_update_time = f"明天 {next_hour}:00"
                        else:
                            next_update_time = f"今天 {next_hour}:00"
                    else:
                        # 使用固定间隔调度
                        next_time = current_datetime + datetime.timedelta(hours=self.update_interval)
                        next_update_time = next_time.strftime('%Y-%m-%d %H:%M:%S')

                    # 将币种列表格式化为每个币种一行，使用序号
                    coins_text = "\n".join([f"{i + 1}. {coin}" for i, coin in enumerate(self.selected_coins)])

                    message = f"选币策略执行结果\n\n"
                    message += f"选币模式: {self.selection_mode}\n"
                    message += f"时间周期: {self.timeframe}\n"
                    message += f"选中币种:\n{coins_text}\n"
                    message += f"选币时间: {update_time}\n"
                    message += f"下次更新时间: {next_update_time}"

                    notifier.send_text(message)
                    self.logger.info("已发送选币结果通知")
                except Exception as e:
                    self.logger.error(f"发送选币结果通知失败: {str(e)}")

        except Exception as e:
            self.logger.error(f"输出选币结果到文件失败: {str(e)}")

    def select_coins(self):
        """
        执行选币逻辑

        Returns:
            list: 选中的币种列表
        """
        self.logger.info("开始执行选币...")

        # 获取所有可交易的U本位永续合约
        all_symbols = self.get_tradable_usd_perpetuals()
        self.logger.info(f"获取到{len(all_symbols)}个可交易的U本位永续合约")

        # 应用黑名单和白名单过滤
        if self.whitelist:
            filtered_symbols = [s for s in all_symbols if s in self.whitelist]
            self.logger.info(f"应用白名单过滤后剩余{len(filtered_symbols)}个币种")
        else:
            filtered_symbols = [s for s in all_symbols if s not in self.blacklist]
            self.logger.info(f"应用黑名单过滤后剩余{len(filtered_symbols)}个币种")

        # 获取24小时交易量并过滤低交易量币种
        volume_filtered = self.filter_by_volume(filtered_symbols)
        bfb = ( len(volume_filtered) / len(filtered_symbols) ) * 100
        self.logger.info(f"合约总计{len(filtered_symbols)}个币种，交易量过滤后剩余{len(volume_filtered)}个币种,过滤后百分比{bfb}%")

        if not volume_filtered:
            self.logger.warning("过滤后没有符合条件的币种，返回空列表")
            return []



        # 计算各币种的多维度指标
        coin_metrics = self.calculate_metrics(volume_filtered)

        # 根据综合评分排序并选择前N个币种
        sorted_coins = sorted(coin_metrics, key=lambda x: x['score'], reverse=True)

        # 输出详细的选币结果
        self.logger.info("选币评分结果:")
        for coin in sorted_coins[:min(10, len(sorted_coins))]:
            self.logger.info(f"{coin['symbol']}: 总分={coin['score']:.2f}, "
                             f"交易量={coin['volume_score']:.2f}, "
                             f"波动性={coin['volatility_score']:.2f}, "
                             f"趋势={coin['trend_score']:.2f}, "
                             f"动量={coin['momentum_score']:.2f}")

        # 返回选中的币种
        selected = [coin['symbol'] for coin in sorted_coins[:self.num_coins]]
        return selected

    def get_selected_coins(self):
        """
        获取当前选中的币种列表

        Returns:
            list: 选中的币种列表
        """
        return self.selected_coins

    def get_tradable_usd_perpetuals(self):
        """
        获取所有可交易的U本位永续合约

        Returns:
            list: 可交易的U本位永续合约列表
        """
        try:
            self.logger.info("正在获取所有可交易的U本位永续合约...")

            # 获取所有合约信息
            instruments = self.trader.get_instruments("SWAP")

            if not instruments:
                self.logger.warning("未获取到任何合约信息")
                return []

            # 筛选U本位永续合约
            usd_perpetuals = []
            for instrument in instruments:
                try:
                    if instrument['ctType'] == 'linear' and instrument['state'] == 'live':
                        symbol = instrument['instId']
                        if symbol.endswith('-USDT-SWAP'):
                            usd_perpetuals.append(symbol)
                except KeyError as e:
                    self.logger.warning(f"合约信息缺少关键字段: {e}")
                    continue

            self.logger.info(f"成功获取{len(usd_perpetuals)}个可交易的U本位永续合约")
            return usd_perpetuals
        except Exception as e:
            self.logger.error(f"获取可交易合约失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []

    def filter_by_volume(self, symbols):
        """
        根据24小时交易量过滤币种

        Args:
            symbols: 币种列表

        Returns:
            list: 交易量符合条件的币种列表
        """
        filtered_symbols = []

        try:
            # 获取24小时交易量数据
            tickers = self.trader.fetch_market_tickers("SWAP")
            # 创建交易量查询字典
            volume_dict = {ticker['instId']: float(ticker['volCcy24h']) for ticker in tickers}

            # 过滤低交易量币种
            for symbol in symbols:
                if symbol in volume_dict and volume_dict[symbol] >= self.min_volume_usd:
                    filtered_symbols.append(symbol)



            return filtered_symbols
        except Exception as e:
            self.logger.error(f"交易量过滤失败: {str(e)}")
            return symbols  # 出错时返回原始列表

    def calculate_metrics(self, symbols):
        """
        计算各币种的多维度指标

        Args:
            symbols: 币种列表

        Returns:
            list: 包含各币种指标和评分的列表
        """
        coin_metrics = []

        # 获取BTC数据作为基准
        btc_klines = self.trader.fetch_ohlcv("BTC-USDT-SWAP", self.timeframe, 100)
        btc_df = None
        if btc_klines and len(btc_klines) > 30:
            # 创建DataFrame并指定列名
            btc_df = pd.DataFrame(btc_klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            btc_df['close'] = btc_df['close'].astype(float)

        # 计算每个币种的指标
        for i, symbol in enumerate(symbols):
            try:
                # 添加请求间隔，避免API请求过于频繁
                if i > 0:
                    time.sleep(1)  # 每次请求间隔1秒

                self.logger.info(f"正在获取第{i + 1}/{len(symbols)}个币种 {symbol} 的K线数据")

                # 获取K线数据
                klines = self.trader.fetch_ohlcv(symbol, self.timeframe, 100)

                if not klines or len(klines) < 30:
                    self.logger.warning(f"{symbol} K线数据不足，跳过")
                    continue

                # 创建DataFrame并指定列名
                df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

                # 转换数据类型
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)

                # 计算各维度指标
                volume_score = self.calculate_volume_score(df)
                volatility_score = self.calculate_volatility_score(df)
                trend_score = self.calculate_trend_score(df)
                momentum_score = self.calculate_momentum_score(df)
                correlation_score = 0.5  # 默认值

                # 如果有BTC数据，计算相关性
                if btc_df is not None:
                    correlation_score = self.calculate_correlation_score(df, btc_df)

                # 计算综合评分
                score = (
                        volume_score * self.weights['volume'] +
                        volatility_score * self.weights['volatility'] +
                        trend_score * self.weights['trend'] +
                        momentum_score * self.weights['momentum'] +
                        correlation_score * self.weights['correlation']
                )

                # 添加到结果列表
                coin_metrics.append({
                    'symbol': symbol,
                    'volume_score': volume_score,
                    'volatility_score': volatility_score,
                    'trend_score': trend_score,
                    'momentum_score': momentum_score,
                    'correlation_score': correlation_score,
                    'score': score
                })

            except Exception as e:
                self.logger.error(f"计算{symbol}指标失败: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())

        return coin_metrics

    def calculate_volume_score(self, df):
        """
        计算交易量评分

        Args:
            df: K线数据DataFrame

        Returns:
            float: 交易量评分(0-1)
        """
        # 计算近期交易量变化
        recent_volume = df['volume'].iloc[-5:].mean()
        past_volume = df['volume'].iloc[-20:-5].mean()

        # 避免除零错误
        if past_volume == 0:
            volume_change = 1
        else:
            volume_change = recent_volume / past_volume

        # 计算交易量稳定性
        volume_stability = 1 - min(1, df['volume'].iloc[-20:].std() / df['volume'].iloc[-20:].mean())

        # 综合评分
        score = (volume_change * 0.7 + volume_stability * 0.3)

        # 标准化到0-1范围
        return min(1, max(0, score / 2))

    def calculate_volatility_score(self, df):
        """
        计算波动性评分

        Args:
            df: K线数据DataFrame

        Returns:
            float: 波动性评分(0-1)
        """
        # 计算ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(self.atr_period).mean().iloc[-1]

        # 计算价格
        price = df['close'].iloc[-1]

        # 计算相对波动率
        relative_volatility = atr / price

        # 根据选币模式调整评分
        if self.selection_mode == 'trend':
            # 趋势模式下，中等波动性得分最高
            score = 1 - abs(relative_volatility - 0.02) / 0.02
        elif self.selection_mode == 'oscillation':
            # 震荡模式下，高波动性得分最高
            score = min(1, relative_volatility / 0.03)
        else:
            # 综合模式，适中波动性
            score = 1 - abs(relative_volatility - 0.025) / 0.025

        return min(1, max(0, score))

    def calculate_trend_score(self, df):
        """
        计算趋势评分

        Args:
            df: K线数据DataFrame

        Returns:
            float: 趋势评分(0-1)
        """
        # 计算EMA
        df['fast_ema'] = df['close'].ewm(span=self.fast_ema, adjust=False).mean()
        df['slow_ema'] = df['close'].ewm(span=self.slow_ema, adjust=False).mean()

        # 计算趋势方向和强度
        ema_distance = (df['fast_ema'] - df['slow_ema']) / df['slow_ema']
        trend_direction = ema_distance.iloc[-1]

        # 计算趋势一致性
        price_change = (df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]

        # 趋势一致性评分
        if (trend_direction > 0 and price_change > 0) or (trend_direction < 0 and price_change < 0):
            consistency = 1
        else:
            consistency = 0

        # 趋势强度评分
        strength = min(1, abs(trend_direction) / 0.05)

        # 根据选币模式调整评分
        if self.selection_mode == 'trend':
            # 趋势模式下，强趋势得分高
            score = strength * 0.7 + consistency * 0.3
        elif self.selection_mode == 'oscillation':
            # 震荡模式下，弱趋势得分高
            score = (1 - strength) * 0.7 + (1 - consistency) * 0.3
        else:
            # 综合模式
            score = strength * 0.5 + consistency * 0.5

        return score

    def calculate_momentum_score(self, df):
        """
        计算动量评分

        Args:
            df: K线数据DataFrame

        Returns:
            float: 动量评分(0-1)
        """
        # 计算RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        # 计算MACD
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal

        # MACD方向和强度
        macd_direction = 1 if histogram.iloc[-1] > 0 else -1
        macd_strength = min(1, abs(histogram.iloc[-1]) / 0.01)

        # 根据选币模式调整评分
        if self.selection_mode == 'trend':
            # 趋势模式下，强动量得分高
            if macd_direction > 0:  # 上升趋势
                rsi_score = current_rsi / 100  # RSI越高越好
            else:  # 下降趋势
                rsi_score = (100 - current_rsi) / 100  # RSI越低越好

            score = rsi_score * 0.5 + macd_strength * 0.5

        elif self.selection_mode == 'oscillation':
            # 震荡模式下，RSI在中间区域得分高
            rsi_score = 1 - abs(current_rsi - 50) / 50

            # 震荡模式下，MACD方向变化频繁得分高
            macd_changes = (np.diff(np.sign(histogram.iloc[-10:])) != 0).sum()
            macd_change_score = min(1, macd_changes / 5)

            score = rsi_score * 0.7 + macd_change_score * 0.3

        else:
            # 综合模式
            if macd_direction > 0:  # 上升趋势
                if current_rsi < 70:  # 未超买
                    rsi_score = current_rsi / 70
                else:  # 超买
                    rsi_score = (100 - current_rsi) / 30
            else:  # 下降趋势
                if current_rsi > 30:  # 未超卖
                    rsi_score = (100 - current_rsi) / 70
                else:  # 超卖
                    rsi_score = current_rsi / 30

            score = rsi_score * 0.6 + macd_strength * 0.4

        return score

    def calculate_correlation_score(self, df, btc_df):
        """
        计算与BTC的相关性评分

        Args:
            df: 币种K线数据DataFrame
            btc_df: BTC K线数据DataFrame

        Returns:
            float: 相关性评分(0-1)
        """
        try:
            # 确保两个DataFrame长度相同
            min_length = min(len(df), len(btc_df))
            coin_returns = df['close'].iloc[-min_length:].pct_change().dropna()
            btc_returns = btc_df['close'].iloc[-min_length:].pct_change().dropna()

            # 计算相关系数
            correlation = coin_returns.corr(btc_returns)

            # 根据选币模式调整评分
            if self.selection_mode == 'trend':
                # 趋势模式下，高相关性得分高
                score = (correlation + 1) / 2
            elif self.selection_mode == 'oscillation':
                # 震荡模式下，低相关性得分高
                score = 1 - (correlation + 1) / 2
            else:
                # 综合模式，中等相关性得分高
                score = 1 - abs(correlation - 0.3)

            return min(1, max(0, score))
        except Exception as e:
            self.logger.error(f"计算相关性失败: {str(e)}")
            return 0.5  # 出错时返回中间值

