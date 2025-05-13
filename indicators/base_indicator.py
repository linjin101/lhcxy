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

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Union, Dict, List, Optional, Any

class BaseIndicator(ABC):
    """
    指标基类：所有技术指标的抽象基类
    定义了指标计算的标准接口和通用功能
    """
    
    def __init__(self, name: str):
        """
        初始化指标基类
        
        Args:
            name: 指标名称
        """
        self.name = name
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        计算指标，必须由子类实现
        
        Args:
            df: 包含OHLCV数据的DataFrame
            **kwargs: 其他参数
            
        Returns:
            添加了指标列的DataFrame
        """
        pass
    
    def __str__(self) -> str:
        """指标描述"""
        return f"{self.name} 指标"
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """
        验证DataFrame是否包含计算指标所需的数据
        
        Args:
            df: 输入的DataFrame
            
        Returns:
            bool: 是否验证通过
        """
        # 检查基本的OHLCV列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                return False
        return True
    
    def get_output_column_names(self) -> List[str]:
        """
        获取该指标将输出的列名列表
        
        Returns:
            List[str]: 输出列名列表
        """
        return [self.name]
    
    def get_min_length(self) -> int:
        """
        获取计算此指标需要的最小数据长度
        
        Returns:
            int: 最小数据长度
        """
        return 1  # 默认值，子类应覆盖此方法
    
    def get_description(self) -> str:
        """
        获取指标的详细描述
        
        Returns:
            str: 指标描述
        """
        return "基础技术指标" 