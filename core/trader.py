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

import ccxt
from pprint import pprint
import pandas as pd
from core.logger_manager import logger_manager
import time
from datetime import datetime
from core.retry_utils import retry


class OkxTrader:
    def __init__(self, api_key, secret_key, passphrase):
        """
        初始化OKX交易类
        
        Args:
            api_key: OKX API密钥
            secret_key: OKX API密钥
            passphrase: OKX API密码
        """
        self.exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': secret_key,
            'password': passphrase,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',  # 默认使用永续合约
            }
        })
        
        # 获取系统日志记录器
        self.logger = logger_manager.get_system_logger()
        # 获取交易日志记录器
        self.trade_logger = logger_manager.get_trade_logger()
        
        # 记录初始化日志
        self.logger.info("OkxTrader初始化完成，运行环境: 实盘环境")
    
    @retry(max_retries=3, base_delay=3.0)
    def close_position(self, symbol):
        """以市场价进行平仓"""
        self.logger.info(f'开始以市场价平仓 {symbol}')
        params = {
            'instId': symbol,
            'mgnMode': 'cross',
        }

        position = self.exchange.fetch_position(symbol)
        if position:
            if float(position['contracts']) > 0:
                self.logger.info(f"持仓方向: {position['side']}")
                side = position['side']
                if side == 'long':
                    params.update({'posSide': 'long'})
                elif side == 'short':
                    params.update({'posSide': 'short'})

                try:
                    order = self.exchange.private_post_trade_close_position(params=params)
                    logger_manager.log_trade(
                        "close_all", 
                        symbol, 
                        "market", 
                        float(position['contracts']), 
                        float(position['markPrice']),
                        order.get('id', 'unknown'),
                        {"side": side, "position_value": float(position['notional'])}
                    )
                    self.logger.info(f"平仓成功: {order}")
                    return order
                except Exception as e:
                    self.logger.error(f"平仓失败: {str(e)}")
                    raise
        else:
            self.logger.warning(f"{symbol}没有持仓，无法执行平仓")
        return None

    @retry(max_retries=3, base_delay=3.0)
    def create_order(self, symbol, side, amount, type='market'):
        """
        创建订单（开仓）
        
        Args:
            symbol: 交易对
            side: 交易方向，'buy'或'sell'
            amount: 数量
            type: 订单类型，默认为'market'（市价单）
        """
        self.logger.info(f"开始创建{side}订单 - {symbol} - 数量: {amount} - 类型: {type}")

        pos_side = ''
        if side == 'sell':
            pos_side = 'short'
        elif side == 'buy':
            pos_side = 'long'

        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type=type,
                side=side,
                amount=amount,
                params={
                    'tdMode': 'cross',  # 全仓模式
                    'posSide': pos_side  # 多仓 or 空仓
                }
            )
            # 记录交易日志
            price = order.get('price', order.get('average', 0))
            if not price and type == 'market':
                # 市价单可能没有价格信息，尝试获取当前价格
                price = self.fetch_market_price(symbol)
            
            logger_manager.log_trade(
                "open", 
                symbol, 
                side, 
                amount, 
                price,
                order.get('id', 'unknown'),
                {"pos_side": pos_side, "order_type": type}
            )
            
            self.logger.info(f"{side}订单已提交: id:{order.get('id', 'unknown')}")
            return order
        except Exception as e:
            error_msg = f"创建订单失败: {str(e)}"
            self.logger.error(error_msg)

            # 使用静态方法发送错误通知
            from core.notification_manager import NotificationManager
            NotificationManager.send_system_error(
                error_msg,
                f"{symbol} create_order 订单创建错误"
            )

            # 继续抛出异常
            raise

    @retry(max_retries=3, base_delay=3.0)
    def close_long_position(self, symbol, amount):
        """平多仓"""
        self.logger.info(f'开始平多仓 {symbol} - 数量: {amount}')
        position = self.exchange.fetch_position(symbol)
        if position:
            try:
                close_long = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side='sell',  # 卖出平多
                    amount=amount,
                    params={
                        'tdMode': 'cross',
                        'posSide': 'long',
                        'reduceOnly': True  # 仅平仓
                    }
                )
                # 记录交易日志
                price = position.get('markPrice', 0)
                logger_manager.log_trade(
                    "close", 
                    symbol, 
                    "sell", 
                    amount, 
                    price,
                    close_long.get('id', 'unknown'),
                    {"pos_side": "long", "entryPrice": position.get('entryPrice', 0)}
                )
                
                self.logger.info(f"平多仓订单已提交: {close_long.get('id', 'unknown')}")
                return close_long
            except Exception as e:
                error_msg = f"平多仓失败: {str(e)}"
                self.logger.error(error_msg)
                # 使用静态方法发送错误通知
                from core.notification_manager import NotificationManager
                NotificationManager.send_system_error(
                    error_msg,
                    f"{symbol} close_long_position 订单创建错误"
                )

                # 继续抛出异常
                raise
        else:
            self.logger.warning(f'当前{symbol}没有仓位，无法执行平仓')
            return None

    @retry(max_retries=3, base_delay=3.0)
    def close_short_position(self, symbol, amount):
        """平空仓"""
        self.logger.info(f'开始平空仓 {symbol} - 数量: {amount}')
        position = self.exchange.fetch_position(symbol)
        if position:
            try:
                close_short = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side='buy',  # 买入平空
                    amount=amount,
                    params={
                        'tdMode': 'cross',
                        'posSide': 'short',
                        'reduceOnly': True  # 仅平仓
                    }
                )
                # 记录交易日志
                price = position.get('markPrice', 0)
                logger_manager.log_trade(
                    "close", 
                    symbol, 
                    "buy", 
                    amount, 
                    price,
                    close_short.get('id', 'unknown'),
                    {"pos_side": "short", "entryPrice": position.get('entryPrice', 0)}
                )
                
                self.logger.info(f"平空仓订单已提交: {close_short.get('id', 'unknown')}")
                return close_short
            except Exception as e:
                error_msg = f"平空仓失败: {str(e)}"
                self.logger.error(error_msg)

                # 使用静态方法发送错误通知
                from core.notification_manager import NotificationManager
                NotificationManager.send_system_error(
                    error_msg,
                    f"{symbol} close_short_position 订单创建错误"
                )

                # 继续抛出异常
                raise
        else:
            self.logger.warning(f'当前{symbol}没有仓位，无法执行平仓')
            return None


    @retry(max_retries=3, base_delay=3.0)
    def fetch_position(self, symbol):
        """获取持仓信息"""
        self.logger.info(f'获取持仓信息:{symbol}')

        try:
            # 获取持仓信息
            position = self.exchange.fetch_position(symbol)
            
            # 记录详细的API返回
            self.logger.debug(f"API返回的持仓信息: {position}")
            
            # 检查获取到的持仓信息
            result = None
            
            if position and position.get('contracts', 0) > 0:
                # 检查持仓的交易对是否和请求的交易对匹配
                inst_id = position['info'].get('instId', '')
                
                self.logger.info(f"持仓的交易对: {inst_id}, 请求的交易对: {symbol}")
                
                if inst_id == symbol:
                    self.logger.info(f"持仓方向: {position['side']}")
                    self.logger.info(f"持仓数量: {position['contracts']}")
                    self.logger.info(f"入场价格: {position['entryPrice']}")
                    self.logger.info(f"未实现盈亏: {position['unrealizedPnl']}")
                    
                    # 确保position对象中包含symbol信息和规范化的入场价格键名
                    position['symbol'] = symbol
                    
                    # 记录持仓日志
                    additional_info = {
                        "entryPrice": position['entryPrice'],
                        "mark_price": position['markPrice'],
                        "unrealized_pnl": position['unrealizedPnl'],
                        "leverage": position.get('leverage', 1)
                    }
                    logger_manager.log_trade(
                        "position", 
                        symbol, 
                        position['side'], 
                        float(position['contracts']), 
                        position['markPrice'],
                        additional_info=additional_info
                    )
                    
                    result = position
                else:
                    # 如果持仓的交易对和请求的不一致，则视为没有该交易对的仓位
                    self.logger.warning(f"警告：API返回的持仓交易对({inst_id})与请求的交易对({symbol})不匹配")
                    self.logger.info(f"{symbol}没有仓位，忽略API返回的其他交易对持仓")
            else:
                self.logger.info(f"{symbol}没有仓位")
        except Exception as e:
            self.logger.error(f"获取持仓信息时发生错误: {str(e)}")
            result = None
        
        return result

    # 新增方法，获取所有持仓
    @retry(max_retries=3, base_delay=3.0)
    def fetch_all_positions(self):
        """获取所有持仓信息"""
        self.logger.info("获取所有持仓信息")
        try:
            positions = self.exchange.fetch_positions()
            self.logger.info(f"当前所有持仓:")
            for pos in positions:
                if pos and pos.get('contracts', 0) > 0:
                    inst_id = pos['info'].get('instId', '')
                    side = pos.get('side', '')
                    contracts = pos.get('contracts', 0)
                    self.logger.info(f"交易对: {inst_id}, 方向: {side}, 数量: {contracts}")
                    
                    # 记录每个持仓的日志
                    additional_info = {
                        "entryPrice": pos.get('entryPrice', 0),
                        "mark_price": pos.get('markPrice', 0),
                        "unrealized_pnl": pos.get('unrealizedPnl', 0),
                        "leverage": pos.get('leverage', 1)
                    }
                    logger_manager.log_trade(
                        "position", 
                        inst_id, 
                        side, 
                        float(contracts), 
                        pos.get('markPrice', 0),
                        additional_info=additional_info
                    )
            return positions
        except Exception as e:
            self.logger.error(f"获取所有持仓信息时发生错误: {str(e)}")
            return []

    @retry(max_retries=3, base_delay=3.0)
    def set_leverage(self, symbol, leverage=1):
        """设置杠杆倍数"""
        self.logger.info(f"设置杠杆倍数 - {symbol} - {leverage}倍")
        try:
            # 设置杠杆
            self.exchange.set_leverage(leverage, symbol, params={'mgnMode': 'cross'})  # 全仓模式
            self.logger.info(f"已发送杠杆设置请求: {leverage}倍")
            
            # 验证杠杆是否设置成功
            try:
                # 查询当前持仓信息以验证杠杆设置
                position_info = self.fetch_account_position(symbol)
                
                if position_info and 'data' in position_info and len(position_info['data']) > 0:
                    # 从返回的持仓信息中获取杠杆值
                    current_leverage = None
                    for pos in position_info['data']:
                        if pos.get('instId') == symbol:
                            current_leverage = int(pos.get('lever', '0'))
                            break
                    
                    if current_leverage is not None:
                        if current_leverage == leverage:
                            self.logger.info(f"杠杆设置成功验证: {symbol} 当前杠杆已设置为 {current_leverage}倍")
                        else:
                            self.logger.warning(f"杠杆设置异常: 请求设置为{leverage}倍，但当前杠杆为{current_leverage}倍")
                            # 重试一次
                            self.logger.info(f"尝试再次设置杠杆为{leverage}倍...")
                            self.exchange.set_leverage(leverage, symbol, params={'mgnMode': 'cross'})
                else:
                    self.logger.info(f"无法验证杠杆设置，无持仓信息返回，但已发送设置请求")
            except Exception as e:
                self.logger.warning(f"验证杠杆设置时出错: {str(e)}")
            
            # 记录杠杆设置日志
            logger_manager.log_trade(
                "set_leverage", 
                symbol, 
                "cross", 
                0, 
                0,
                additional_info={"leverage": leverage}
            )
            return True
        except Exception as e:
            self.logger.error(f"设置杠杆失败: {str(e)}")
            return False

    @retry(max_retries=3, base_delay=3.0)
    def get_account(self):
        """获取账户余额"""
        self.logger.info("获取账户余额")
        try:
            # 打印完整余额信息
            account_balance = self.exchange.private_get_account_balance({'ccy': 'USDT'})
            
            # 提取关键余额信息并记录
            if account_balance and 'data' in account_balance and account_balance['data']:
                balance_data = account_balance['data'][0]
                if 'details' in balance_data and balance_data['details']:
                    details = balance_data['details'][0]
                    total_cash = details.get('cashBal', '0')
                    avail_bal = details.get('availBal', '0')
                    frozen_bal = details.get('frozenBal', '0')
                    
                    self.logger.info(f"账户总金额: {total_cash}")
                    self.logger.info(f"可用余额: {avail_bal}")
                    self.logger.info(f"冻结金额: {frozen_bal}")
                    
                    # 记录账户余额日志
                    logger_manager.log_trade(
                        "account_balance", 
                        "USDT", 
                        "balance", 
                        0, 
                        0,
                        additional_info={
                            "total": total_cash,
                            "available": avail_bal,
                            "frozen": frozen_bal
                        }
                    )
            
            return account_balance
        except Exception as e:
            self.logger.error(f"获取账户余额失败: {str(e)}")
            raise

    @retry(max_retries=3, base_delay=3.0)
    def fetch_account_position(self, symbol):
        """获取账户持仓详情"""
        self.logger.info(f'获取合约信息:{symbol}')
        params = {
                'instId': symbol,
                'instType':'SWAP'
        }

        try:
            account_data = self.exchange.private_get_account_positions(params)
            self.logger.debug(f"账户持仓详情: {account_data}")
            return account_data
        except Exception as e:
            self.logger.error(f"获取账户持仓详情失败: {str(e)}")
            raise
    
    @retry(max_retries=3, base_delay=3.0)
    def fetch_ticker(self, symbol):
        """获取最新行情数据"""
        try:
            ticker = self.exchange.publicGetPublicMarkPrice({"instType": "SWAP", "instId": symbol})
            
            # 记录市场数据日志
            if ticker and 'data' in ticker and ticker['data']:
                mark_price = ticker['data'][0].get('markPx', '0')
                logger_manager.log_market(
                    symbol, 
                    "ticker", 
                    f"最新标记价格: {mark_price}"
                )
            
            return ticker
        except Exception as e:
            self.logger.error(f"获取行情数据失败 - {symbol}: {str(e)}")
            raise
    
    @retry(max_retries=3, base_delay=3.0)
    def fetch_market_price(self, symbol):
        """
        直接获取最新市场价格
        
        Args:
            symbol: 交易对符号
            
        Returns:
            float: 最新市场价格，失败时返回0
        """
        try:
            ticker = self.fetch_ticker(symbol)
            if ticker and 'data' in ticker and ticker['data']:
                mark_price = float(ticker['data'][0].get('markPx', 0))
                self.logger.debug(f"获取{symbol}最新市场价格: {mark_price}")
                return mark_price
            return 0
        except Exception as e:
            self.logger.error(f"获取市场价格失败 - {symbol}: {str(e)}")
            return 0
    
    @retry(max_retries=3, base_delay=3.0)
    def fetch_ohlcv(self, symbol, timeframe='1m', limit=300):
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            timeframe: 时间周期，如'1m', '5m', '1h', '1d'等
            limit: 获取的K线数量
        """
        self.logger.info(f"获取K线数据 - {symbol} - {timeframe} - 数量: {limit}")
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # 记录市场数据日志
            if ohlcv and len(ohlcv) > 0:
                latest = ohlcv[-1]
                logger_manager.log_market(
                    symbol, 
                    "kline", 
                    f"最新K线 - 开:{latest[1]} 高:{latest[2]} 低:{latest[3]} 收:{latest[4]} 量:{latest[5]}"
                )
            
            return ohlcv
        except Exception as e:
            self.logger.error(f"获取K线数据失败 - {symbol} - {timeframe}: {str(e)}")
            raise
    
    @retry(max_retries=3, base_delay=3.0)
    def fetch_all_ohlcv(self, symbol, timeframe='1m', limit=2000, max_retries=3, retry_delay=1):
        """
        分批获取更多K线数据
        
        由于交易所API通常限制单次请求的K线数量（如OKX限制为300条），
        该方法通过多次请求并合并结果来获取更多的历史K线数据。
        
        Args:
            symbol: 交易对
            timeframe: 时间周期，如'1m', '5m', '1h', '1d'等
            limit: 需要获取的K线总数量
            max_retries: 每批请求的最大重试次数
            retry_delay: 重试间隔（秒）
            
        Returns:
            list: 包含K线数据的列表，按时间从早到晚排序
        """
        self.logger.info(f"批量获取K线数据 - {symbol} - {timeframe} - 目标数量: {limit}")
        
        all_candles = []
        single_request_limit = 300  # OKX API单次请求限制
        
        # 首先获取最新的K线数据
        try:
            # 获取最新的一批数据
            latest_candles = self.exchange.fetch_ohlcv(symbol, timeframe, limit=single_request_limit)
            if not latest_candles:
                self.logger.warning("无法获取K线数据")
                return []
                
            self.logger.info(f"已获取最新的 {len(latest_candles)} 条K线数据")
            all_candles.extend(latest_candles)
            
            # 如果目标数量大于已获取的数量，继续获取历史数据
            remaining = limit - len(all_candles)
            
            # 如果需要获取更多数据
            while remaining > 0 and len(latest_candles) > 0:
                # 获取当前批次中最早的时间戳
                earliest_timestamp = min(candle[0] for candle in latest_candles)
                
                # OKX 要求使用毫秒时间戳
                # 获取早于最早时间戳的数据
                since = earliest_timestamp - (self.get_timeframe_ms(timeframe) * single_request_limit)
                
                self.logger.info(f"获取更早的数据，起始时间: {datetime.fromtimestamp(since/1000).strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 延迟以避免API限流
                time.sleep(2)
                
                # 获取历史数据
                latest_candles = self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe,
                    since=since,
                    limit=single_request_limit
                )
                
                # 检查是否获取到新数据
                if not latest_candles:
                    self.logger.warning("未获取到更多历史数据")
                    break
                    
                # 检查是否有重叠（避免无限循环）
                new_earliest = min(candle[0] for candle in latest_candles)
                if new_earliest >= earliest_timestamp:
                    self.logger.warning(f"无法获取更早的数据（时间戳重叠），停止获取")
                    break
                
                # 检查获取到的K线是否都早于已有的最早K线
                valid_candles = [c for c in latest_candles if c[0] < earliest_timestamp]
                
                if not valid_candles:
                    self.logger.warning("未获取到更早的K线数据")
                    break
                
                self.logger.info(f"获取到 {len(valid_candles)} 条更早的K线数据")
                all_candles.extend(valid_candles)
                
                # 更新剩余需要获取的数量
                remaining = limit - len(all_candles)
                
                # 如果刚好达到或超过目标数量，退出循环
                if remaining <= 0:
                    break
            
            # 去重并排序
            all_timestamps = {}
            unique_candles = []
            
            for candle in all_candles:
                timestamp = candle[0]
                if timestamp not in all_timestamps:
                    all_timestamps[timestamp] = candle
                    unique_candles.append(candle)
            
            # 按时间戳排序
            sorted_candles = sorted(unique_candles, key=lambda x: x[0])
            
            # 限制返回数量
            result = sorted_candles[:limit]
            
            self.logger.info(f"批量获取K线完成，总计获取 {len(result)}/{limit} 条K线数据")
            
            # 添加日期时间范围信息
            if result:
                start_time = datetime.fromtimestamp(result[0][0]/1000).strftime('%Y-%m-%d %H:%M:%S')
                end_time = datetime.fromtimestamp(result[-1][0]/1000).strftime('%Y-%m-%d %H:%M:%S')
                self.logger.info(f"K线时间范围: {start_time} 至 {end_time}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"批量获取K线数据失败: {str(e)}")
            # 如果已获取部分数据，返回已获取的数据
            if all_candles:
                self.logger.warning(f"返回已获取的 {len(all_candles)} 条K线数据")
                # 确保按时间戳排序
                sorted_candles = sorted(all_candles, key=lambda x: x[0])
                return sorted_candles[:limit]
            else:
                raise
    
    def get_timeframe_ms(self, timeframe):
        """
        将时间周期转换为毫秒数
        
        Args:
            timeframe: 时间周期字符串，如 '1m', '5m', '1h', '1d' 等
            
        Returns:
            int: 对应的毫秒数
        """
        # 提取数字和单位
        import re
        match = re.match(r'(\d+)([mdh])', timeframe)
        if not match:
            self.logger.error(f"无法解析时间周期: {timeframe}")
            return 60000  # 默认返回1分钟
            
        value, unit = int(match.group(1)), match.group(2)
        
        # 转换为毫秒
        if unit == 'm':  # 分钟
            return value * 60 * 1000
        elif unit == 'h':  # 小时
            return value * 60 * 60 * 1000
        elif unit == 'd':  # 天
            return value * 24 * 60 * 60 * 1000
        else:
            self.logger.error(f"未知的时间单位: {unit}")
            return 60000  # 默认返回1分钟

    @retry(max_retries=3, base_delay=3.0)
    def get_order_book(self, symbol, limit=20):
        """获取订单簿数据"""
        self.logger.info(f"获取订单簿 - {symbol} - 深度: {limit}")
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit)
            
            # 记录市场数据日志
            if order_book:
                bids_count = len(order_book.get('bids', []))
                asks_count = len(order_book.get('asks', []))
                logger_manager.log_market(
                    symbol, 
                    "orderbook", 
                    f"买单数量: {bids_count}, 卖单数量: {asks_count}"
                )
            
            return order_book
        except Exception as e:
            self.logger.error(f"获取订单簿失败 - {symbol}: {str(e)}")
            raise

    @retry(max_retries=3, base_delay=3.0)
    def fetch_instrument(self, symbol):
        """
        获取合约规格信息
        
        Args:
            symbol: 交易对符号
            
        Returns:
            dict: 合约规格信息
        """
        self.logger.info(f"获取合约规格 - {symbol}")
        try:
            # 使用OKX API获取合约信息
            params = {
                'instId': symbol,
                'instType':'SWAP'
            }

            response = self.exchange.publicGetPublicInstruments(params)
            
            # 记录合约信息日志
            if response and 'data' in response and response['data']:
                instrument = response['data'][0]
                self.logger.info(f"合约信息 - {symbol} - 最小交易量: {instrument.get('minSz', '0')}, 价格精度: {instrument.get('tickSz', '0')}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"获取合约规格时发生错误: {str(e)}")
            return None

    @retry(max_retries=3, base_delay=3.0)
    def check_position_is_dual_side(self):
        '''
        获取合约持仓设置, 判断是不是双向持仓模型（即可以开多，可以空）
        '''
        accountConfig = self.exchange.privateGetAccountConfig()
        posMode = accountConfig['data'][0]['posMode']

        if posMode !='long_short_mode':
            raise ValueError("当前持仓模式不是双向持仓模式，程序已停止运行。请去官网改为双向持仓。")
        else:
            print('当前持仓模式：双向持仓')