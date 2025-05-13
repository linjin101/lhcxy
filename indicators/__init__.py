# 导入所有指标类，方便使用
from indicators.base_indicator import BaseIndicator
from indicators.moving_average import SimpleMovingAverage, ExponentialMovingAverage, WeightedMovingAverage, HullMovingAverage, MAFactory
from indicators.oscillators import RSI, MACD, Stochastic, BollingerBands, ATR

# 创建工厂函数，根据名称创建指标
def create_indicator(name, **kwargs):
    """
    根据名称创建指标实例
    
    Args:
        name: 指标名称，如'SMA', 'RSI', 'MACD'等
        **kwargs: 指标参数
        
    Returns:
        BaseIndicator: 创建的指标实例
        
    Raises:
        ValueError: 不支持的指标类型
    """
    name = name.upper()
    
    # 移动平均线类
    if name in ['SMA', 'EMA', 'WMA', 'HMA']:
        period = kwargs.get('period', 20)
        source_column = kwargs.get('source_column', 'close')
        return MAFactory.create(name, period, source_column)
    
    # 震荡指标类
    elif name == 'RSI':
        period = kwargs.get('period', 14)
        source_column = kwargs.get('source_column', 'close')
        return RSI(period, source_column)
    
    elif name == 'MACD':
        fast_period = kwargs.get('fast_period', 12)
        slow_period = kwargs.get('slow_period', 26)
        signal_period = kwargs.get('signal_period', 9)
        source_column = kwargs.get('source_column', 'close')
        return MACD(fast_period, slow_period, signal_period, source_column)
    
    elif name == 'KDJ' or name == 'STOCHASTIC':
        k_period = kwargs.get('k_period', 14)
        d_period = kwargs.get('d_period', 3)
        j_period = kwargs.get('j_period', 3)
        return Stochastic(k_period, d_period, j_period)
    
    elif name == 'BB' or name == 'BOLLINGER':
        period = kwargs.get('period', 20)
        std_dev = kwargs.get('std_dev', 2.0)
        source_column = kwargs.get('source_column', 'close')
        return BollingerBands(period, std_dev, source_column)
    
    elif name == 'ATR':
        period = kwargs.get('period', 14)
        return ATR(period)
    
    # 趋势指标类
    elif name == 'ADX':
        period = kwargs.get('period', 14)
        return ADX(period)
    
    elif name == 'ICHIMOKU':
        tenkan_period = kwargs.get('tenkan_period', 9)
        kijun_period = kwargs.get('kijun_period', 26)
        senkou_span_b_period = kwargs.get('senkou_span_b_period', 52)
        displacement = kwargs.get('displacement', 26)
        return Ichimoku(tenkan_period, kijun_period, senkou_span_b_period, displacement)
    
    elif name == 'PSAR' or name == 'PARABOLICSAR':
        acceleration = kwargs.get('acceleration', 0.02)
        maximum = kwargs.get('maximum', 0.2)
        return ParabolicSAR(acceleration, maximum)
    
    else:
        raise ValueError(f"不支持的指标类型: {name}")

# 便捷函数，计算单个指标
def calculate_indicator(df, name, **kwargs):
    """
    便捷函数，直接计算单个指标并返回结果
    
    Args:
        df: 包含OHLCV数据的DataFrame
        name: 指标名称
        **kwargs: 指标参数
        
    Returns:
        pd.DataFrame: 添加了指标列的DataFrame
    """
    indicator = create_indicator(name, **kwargs)
    return indicator.calculate(df)

# 便捷函数，计算多个指标
def calculate_indicators(df, indicators_config):
    """
    便捷函数，计算多个指标并返回结果
    
    Args:
        df: 包含OHLCV数据的DataFrame
        indicators_config: 指标配置列表，每个元素是一个字典，包含name和params两个键
            例如：[{'name': 'SMA', 'params': {'period': 20}}, {'name': 'RSI', 'params': {'period': 14}}]
            
    Returns:
        pd.DataFrame: 添加了所有指标列的DataFrame
    """
    result_df = df.copy()
    
    for config in indicators_config:
        name = config['name']
        params = config.get('params', {})
        
        indicator = create_indicator(name, **params)
        result_df = indicator.calculate(result_df)
    
    return result_df

# 导出所有可用的指标名称
AVAILABLE_INDICATORS = [
    'SMA', 'EMA', 'WMA', 'HMA',  # 移动平均线指标
    'RSI', 'MACD', 'KDJ', 'BB', 'ATR',  # 震荡指标
    'ADX', 'PSAR'  # 趋势指标
] 