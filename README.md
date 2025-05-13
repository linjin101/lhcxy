# OKX量化交易框架 - 使用指南

## 目录
- [简介](#简介)
- [项目结构](#项目结构)
- [开始使用](#开始使用)
- [策略模型](#策略模型)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

## 简介

OKX量化交易框架是一个基于Python的加密货币量化交易系统，旨在为交易者提供一个易于使用、扩展性强的交易策略开发环境。本框架支持对OKX交易所的各种交易对进行自动化交易，内置多种技术指标和策略模型。

### 特点
- 简单易用：提供详细的示例策略和文档
- 高度可定制：支持自定义策略和参数
- 风险管理：内置仓位管理和风险控制功能
- 交易通知：支持通过企业微信等渠道发送交易通知

## 项目结构

```
02.okx_quant_framework/
├── config/                # 配置文件目录
│   ├── config.py          # 主配置文件
│   └── api_keys.py        # API密钥配置
    └── tp_sl_config.py        # 止盈止损配置
├── core/                  # 核心组件
│   ├── trader.py          # 交易执行接口
│   ├── strategy_template.py # 策略模板基类
│   ├── data_feed.py       # 数据获取模块
│   ├── position_manager.py # 仓位管理
│   ├── notification_manager.py # 通知管理
│   ├── retry_utils.py # 通知管理
│   └── logger_manager.py  # 日志管理
├── indicators/            # 技术指标库
│   ├── moving_average.py  # 移动平均线指标

├── strategies/            # 策略实现目录
│   └── examples/          # 示例策略
│       ├── dual_ema_strategy.py # 双ema策略
│       ├── simple_ma_strategy.py      # 简单均线策略
│       └── ...
├── main.py                # 程序入口点
└── README.md              # 项目说明文档
```

### 核心目录说明

- **config/**: 包含所有配置信息，包括交易参数、API密钥和策略配置
- **core/**: 框架的核心组件，负责交易执行、数据获取和策略执行
- **indicators/**: 技术指标库，提供各种技术分析指标的实现
- **strategies/examples/**: 包含各种示例策略实现，附带详细注释

## 开始使用

### 环境准备

1. 安装Python 3.10.6+和依赖包：
```bash
pip install -r requirements.txt
```

2. 配置API密钥：
   - 在`config/api_keys.py`中填入您的OKX API密钥信息

3. 选择和配置策略：
   - 在`config/config.py`中的`trading_config`设置您要使用的策略名称
   - 根据需要调整该策略的参数配置

### 运行系统

1. 运行交易系统：
```bash
python main.py
```

## 策略模型

### 策略类型

本框架提供了一系列示例策略：

- **简单均线策略**：基于价格与移动平均线的关系生成信号
- **双均线策略**：利用两条不同周期均线的交叉生成信号


所有策略都位于`strategies/examples/`目录，包含详细的注释和说明，便于学习和修改。

### 策略加载机制

系统通过以下流程加载和运行策略：

1. 在`config/config.py`中设置`trading_config['strategy']`指定要使用的策略名称
2. 系统在`main.py`的`STRATEGY_MAPPING`字典中查找对应的映射关系
3. 根据映射信息，动态加载对应的策略模块、类和配置
4. 创建策略实例并运行

例如，如果设置：
```python
trading_config['strategy'] = 'bollinger_bands_strategy'
```

系统会加载`strategies/examples/bollinger_bands_strategy.py`中的`BollingerBandsStrategy`类。

### 自定义策略

要创建自己的策略，可以：

1. 复制一个现有的示例策略作为模板
2. 继承`StrategyTemplate`或`SignalStrategy`基类
3. 实现`generate_signals`方法
4. 在`STRATEGY_MAPPING`中添加新策略的映射

## 配置说明

### 主要配置选项

在`config/config.py`中：

- **trading_config**: 交易基本配置
  - `strategy`: 策略名称
  - `symbol`: 交易对，如'BTC-USDT-SWAP'
  - `timeframe`: 时间周期，如'1h'
  - `is_test`: 是否使用测试模式

- **position_config**: 仓位管理配置
  - `leverage`: 杠杆倍数
  - `risk_percentage`: 风险百分比

- **notification_config**: 通知配置
  - `enabled`: 是否启用通知
  - `wechat_webhook_url`: 企业微信机器人webhook地址

### 策略特定配置

每个策略都有其特定的配置选项，通常以`策略名_config`命名，例如：

```python
# EMA策略参数 (ema_strategy)
dual_ema_strategy_config = {
    'fast_ema_period': 20,
    'slow_ema_period': 60
}
```