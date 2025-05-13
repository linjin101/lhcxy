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

import math
from core.logger_manager import logger_manager

class PositionManager:
    def __init__(self, trader, config):
        """
        初始化仓位管理器
        
        Args:
            trader: OkxTrader实例，用于API调用
            config: 配置信息，包含风险参数等
        """
        self.trader = trader
        self.config = config
        self.contract_info_cache = {}  # 缓存合约信息以减少API调用
        self.logger = logger_manager.get_position_logger()  # 获取专用日志记录器
        
    def get_account_balance(self, currency='USDT'):
        """
        获取账户余额
        
        Args:
            currency: 货币类型，默认USDT
            
        Returns:
            float: 可用余额
        """
        try:
            # 调用API获取账户余额
            account_info = self.trader.get_account()

            # 查找指定货币的可用余额
            if account_info and 'data' in account_info:
                for balance in account_info['data'][0]['details']:
                    if balance['ccy'] == currency:
                        # 账户总金额
                        total_cash = account_info['data'][0]['details'][0]['cashBal']
                        print('账户总金额:', total_cash)

                        # 可用的余额
                        availBal = account_info['data'][0]['details'][0]['availBal']
                        print('可用余额:', availBal)

                        # 已经买b的金额
                        frozenBal = account_info['data'][0]['details'][0]['frozenBal']
                        print('冻结的金额:', frozenBal)

                        return float(availBal)
            
            # 如果找不到，返回0
            print(f"警告: 找不到{currency}的可用余额，返回0")
            return 0
            
        except Exception as e:
            print(f"获取账户余额时发生错误: {str(e)}")
            return 0
        
    def get_contract_info(self, symbol):
        """
        获取合约信息
        
        Args:
            symbol: 交易对符号
            
        Returns:
            dict: 包含最小交易单位、合约面值、价格精度等信息
        """
        # 如果已缓存，则直接返回
        if symbol in self.contract_info_cache:
            return self.contract_info_cache[symbol]
            
        try:
            # 获取合约信息
            instruments = self.trader.fetch_instrument(symbol)
            
            if not instruments or 'data' not in instruments or not instruments['data']:
                print(f"警告: 无法获取{symbol}的合约信息")
                return None
            
            instrument = instruments['data'][0]
            
            # 提取需要的信息
            contract_info = {
                'min_size': float(instrument.get('minSz', '0')),
                'size_increment': float(instrument.get('lotSz', '0')),
                'price_increment': float(instrument.get('tickSz', '0')),
                'contract_value': float(instrument.get('ctVal', '0')),
                'contract_type': instrument.get('instType', ''),
                'face_value': float(instrument.get('ctVal', '1')),  # 合约面值，默认为1
                'max_leverage': float(instrument.get('lever', '100'))  # 最大杠杆，默认为100倍
            }
            
            print(f"合约信息详细数据: {instrument}")
            print(f"提取的关键信息: {contract_info}")

            # 缓存结果
            self.contract_info_cache[symbol] = contract_info
            return contract_info
            
        except Exception as e:
            print(f"获取合约信息时发生错误: {str(e)}")
            return None
        
    def set_leverage(self, symbol, leverage):
        """
        设置交易对的杠杆倍数
        
        Args:
            symbol: 交易对符号
            leverage: 杠杆倍数
            
        Returns:
            bool: 设置是否成功
        """
        try:
            self.logger.info(f"正在为{symbol}设置杠杆倍数: {leverage}倍")
            
            # 调用交易所API设置杠杆
            self.trader.set_leverage(symbol, leverage)
            
            # 验证杠杆是否设置成功
            self.logger.info(f"杠杆设置请求已发送，杠杆值: {leverage}倍")
            
            # 添加重要提示，供排查问题使用
            self.logger.info("注意：如果交易所平台已有该币种的持仓，杠杆设置可能不会立即生效")
            self.logger.info("实际使用的杠杆可能会在下次开仓时生效")
            
            return True
        except Exception as e:
            self.logger.error(f"设置杠杆倍数时发生错误: {str(e)}")
            return False
        
    def get_current_leverage(self, symbol):
        """
        获取当前设置的杠杆倍数
        
        Args:
            symbol: 交易对符号
            
        Returns:
            int: 当前杠杆倍数
        """
        # 从全局position_config配置中获取杠杆设置
        from config.config import position_config
        leverage = position_config.get('leverage', 1)  # 默认使用1倍杠杆（改为安全默认值）
        self.logger.info(f'基础杠杆配置: {leverage}倍')

        
        # 检查交易对特定的杠杆配置
        from config.config import symbol_position_config
        if symbol in symbol_position_config:
            leverage = symbol_position_config[symbol].get('leverage', leverage)
            self.logger.info(f'使用{symbol}特定杠杆配置: {leverage}倍')
        else:
            self.logger.info(f'{symbol}没有特定杠杆配置，使用默认值: {leverage}倍')


        # 获取合约信息中的最大杠杆
        contract_info = self.get_contract_info(symbol)
        if contract_info:
            max_leverage = contract_info.get('max_leverage', 100)
            # 确保不超过最大杠杆
            if leverage > max_leverage:
                self.logger.warning(f'请求的杠杆{leverage}超过最大允许值{max_leverage}，将使用最大允许值')
                leverage = max_leverage
            
        self.logger.info(f'最终使用的杠杆倍数: {leverage}倍')
        return leverage
        
    def calculate_position_size(self, symbol, price, risk_percentage=None):
        """
        计算推荐的仓位大小，考虑杠杆因素
        
        Args:
            symbol: 交易对符号
            price: 当前价格
            risk_percentage: 风险百分比，若为None则使用配置值
            
        Returns:
            float: 计算后的仓位大小（合约数量）
        """
        try:
            # 检查是否使用动态仓位计算
            use_dynamic_position = self.config.get('use_dynamic_position', True)
            if not use_dynamic_position:
                # 使用固定仓位
                fixed_amount = self.config.get('amount', 1)
                self.logger.info(f"使用固定仓位大小: {fixed_amount} 张")
                return fixed_amount
                
            # 以下为动态仓位计算逻辑
            # 获取账户余额
            balance = self.get_account_balance()
            if balance <= 0:
                self.logger.warning("账户余额为0或获取失败，无法计算仓位大小")
                return self.config.get('amount', 1)  # 使用固定仓位作为后备
                
            # 获取风险百分比
            if risk_percentage is None:
                # 从config配置文件中获取position_config和symbol_position_config
                from config.config import position_config, symbol_position_config
                
                # 首先使用默认风险百分比
                risk_percentage = 0.02  # 默认使用2%风险
                
                # 其次从全局position_config中获取
                if 'risk_percentage' in position_config:
                    risk_percentage = position_config.get('risk_percentage')
                    self.logger.info(f"从全局position_config获取风险比例: {risk_percentage}")
                
                # 最后从特定交易对配置中获取，优先级最高
                if symbol in symbol_position_config and 'risk_percentage' in symbol_position_config[symbol]:
                    risk_percentage = symbol_position_config[symbol].get('risk_percentage')
                    self.logger.info(f"从交易对特定配置获取风险比例: {risk_percentage}")

            # debug 测试的时候用较大值
            if self.config.get('is_test', False):
                risk_percentage = 0.3  # 测试环境使用30%的资金
                self.logger.info(f"测试环境，使用测试风险比例: {risk_percentage}")

            # # 测试的时候用，害怕下单的时候金额瞬间变化，会导致下单的数量大于实际可以下单的数量，因为我们要留有余量，下单的时候只拿95%的资金下单，这样万无一失
            # risk_percentage = 0.95

            risk_amount = balance * risk_percentage
            self.logger.info(f"账户余额: {balance}, 风险比例: {risk_percentage}, 风险金额: {risk_amount}")

            
            # 获取合约信息
            contract_info = self.get_contract_info(symbol)
            if not contract_info:
                self.logger.warning(f"无法获取合约信息，使用配置中的固定数量")
                return self.config.get('amount', 1)  # 使用配置中的固定数量作为后备

            # 获取杠杆倍数
            leverage = self.get_current_leverage(symbol)
            self.logger.info(f"计划使用杠杆倍数: {leverage}倍")
            
            # 设置杠杆倍数到交易所
            set_result = self.set_leverage(symbol, leverage)
            if not set_result:
                self.logger.warning(f"警告: 无法设置杠杆倍数，将使用交易所默认杠杆")
            
            # 计算合约数量（基于资金风险和杠杆）
            if price <= 0:
                self.logger.warning("价格无效，无法计算仓位大小")
                return self.config.get('amount', 1)  # 使用固定仓位作为后备
            
            # 获取合约面值
            face_value = contract_info.get('face_value', 1)
            self.logger.info(f"合约面值: {face_value}")
            
            # 计算名义价值 = 价格 × 面值 × 张数
            # 所以张数 = 名义价值 / (价格 × 面值)
            # 名义价值 = 风险金额 × 杠杆
            
            # 考虑杠杆的仓位计算
            nominal_value = risk_amount * leverage
            position_size = nominal_value / (price * face_value)
            
            self.logger.info(f"未调整前的仓位大小: {position_size} 张")
            
            # 调整到合约精度
            position_size = self.adjust_to_precision(symbol, position_size)
            self.logger.info(f"调整精度后的仓位大小: {position_size} 张")
            
            # 验证仓位大小是否合理
            is_valid, reason = self.validate_position_size(symbol, position_size)
            if not is_valid:
                self.logger.warning(f"计算的仓位大小无效: {reason}")
                return self.config.get('amount', 1)  # 使用固定仓位作为后备
                
            return position_size
            
        except Exception as e:
            self.logger.error(f"计算仓位大小时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return self.config.get('amount', 1)  # 使用固定仓位作为后备
        
    def adjust_to_precision(self, symbol, size):
        """
        将仓位大小调整为符合交易所精度要求的值
        
        Args:
            symbol: 交易对符号
            size: 原始仓位大小
            
        Returns:
            float: 调整后的仓位大小
        """
        try:
            contract_info = self.get_contract_info(symbol)
            if not contract_info:
                return size  # 无法获取合约信息，返回原始大小
            
            # 获取大小增量
            size_increment = contract_info.get('size_increment', 0)
            min_size = contract_info.get('min_size', 0)
            
            if size_increment <= 0 or min_size <= 0:
                return size  # 信息无效，返回原始大小
            
            # 计算调整后的大小（向下取整到最近的有效大小）
            adjusted_size = math.floor(size / size_increment) * size_increment
            
            # 确保至少达到最小大小
            adjusted_size = max(adjusted_size, min_size)
            
            return adjusted_size
            
        except Exception as e:
            self.logger.error(f"调整精度时发生错误: {str(e)}")
            return size

    def validate_position_size(self, symbol, size):
        """
        验证仓位大小是否符合安全标准和交易所规则
        
        Args:
            symbol: 交易对符号
            size: 仓位大小
            
        Returns:
            tuple: (是否有效(bool), 无效原因(str))
        """
        try:
            # 基本检查
            if size <= 0:
                return False, "仓位大小必须大于0"
            
            # 获取合约信息
            contract_info = self.get_contract_info(symbol)
            if not contract_info:
                return True, ""  # 无法验证，假设有效
            
            # 检查是否满足最小大小要求
            min_size = contract_info.get('min_size', 0)
            if min_size > 0 and size < min_size:
                return False, f"仓位大小 {size} 小于最小要求 {min_size}"
            
            # 获取最大仓位限制（如果配置中有）
            position_config = self.config.get('position_config', {})
            max_position_size = position_config.get('max_position_size', float('inf'))
            
            if size > max_position_size:
                return False, f"仓位大小 {size} 超过最大限制 {max_position_size}"
            
            # 验证通过
            return True, ""
            
        except Exception as e:
            self.logger.error(f"验证仓位大小时发生错误: {str(e)}")
            return False, f"验证过程中发生错误: {str(e)}"
        
    def get_optimal_position_size(self, symbol, price, side):
        """
        获取综合考虑各种因素后的最优仓位大小
        
        Args:
            symbol: 交易对符号
            price: 当前价格
            side: 交易方向，'buy'或'sell'
            
        Returns:
            float: 最优仓位大小
        """
        try:
            # 获取基本仓位大小
            position_size = self.calculate_position_size(symbol, price)
            
            # 获取当前持仓信息
            current_position = self.trader.fetch_position(symbol)
            
            # 检查是否需要根据当前持仓进行调整
            # 在这个基础版本中，我们暂时不做特殊调整
            
            # 返回计算结果
            return position_size
            
        except Exception as e:
            self.logger.error(f"获取最优仓位大小时发生错误: {str(e)}")
            # 出错时使用配置中的固定数量
            return self.config.get('amount', 1) 