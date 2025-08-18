# 核心交易引擎 v2.0.0

## 🎯 概述

核心交易引擎是量化交易系统v2.0的核心组件，基于聚宽数据源，提供完整的交易执行、策略管理、风险控制和实时行情功能。

## 🏗️ 架构组成

### 1. 增强版交易服务 (Enhanced Trading Service)
- **文件**: `services/enhanced_trading_service.py`
- **功能**: 投资组合管理、持仓管理、订单管理、风险控制
- **特点**: 
  - 实时行情集成
  - 自动风险检查
  - 智能订单执行
  - 完整的交易闭环

### 2. 策略执行引擎 (Strategy Executor)
- **文件**: `services/strategy_executor.py`
- **功能**: 策略信号处理、自动交易执行、风险管理
- **特点**:
  - 异步信号处理
  - 智能仓位管理
  - 实时风险监控
  - 执行结果记录

### 3. 实时行情服务 (Market Data Service)
- **文件**: `services/market_data_service.py`
- **功能**: 实时行情推送、WebSocket数据服务、市场数据管理
- **特点**:
  - WebSocket实时推送
  - 多股票订阅管理
  - 市场指数监控
  - 智能缓存机制

## 🚀 核心功能

### 交易执行
- **市价单/限价单**: 支持多种订单类型
- **自动执行**: 策略信号自动转换为交易订单
- **风险检查**: 下单前自动进行风险验证
- **持仓管理**: 实时更新持仓市值和盈亏

### 策略管理
- **信号生成**: 支持多种策略类型（均线交叉、KDJ+MACD等）
- **自动执行**: 策略信号自动进入执行队列
- **置信度管理**: 根据信号置信度调整执行数量
- **策略监控**: 实时监控策略运行状态

### 风险控制
- **仓位限制**: 单只股票最大仓位20%
- **风险指标**: 实时计算最大回撤、夏普比率等
- **预警系统**: 风险超限自动预警
- **动态调整**: 根据市场情况动态调整风险参数

### 实时行情
- **WebSocket推送**: 实时推送股票行情和指数数据
- **多股票订阅**: 支持同时订阅多只股票
- **市场概览**: 实时市场状态和指数表现
- **数据缓存**: 智能缓存减少API调用

## 📊 数据结构

### MarketData (市场数据)
```python
@dataclass
class MarketData:
    stock_code: str          # 股票代码
    current_price: float     # 当前价格
    change: float           # 涨跌额
    change_pct: float      # 涨跌幅
    volume: int            # 成交量
    amount: float          # 成交额
    high: float           # 最高价
    low: float            # 最低价
    open: float           # 开盘价
    prev_close: float     # 昨收价
    timestamp: datetime   # 时间戳
```

### Position (持仓)
```python
@dataclass
class Position:
    stock_code: str          # 股票代码
    stock_name: str          # 股票名称
    quantity: int            # 持仓数量
    avg_price: float         # 平均成本
    current_price: float     # 当前价格
    market_value: float      # 市值
    unrealized_pnl: float    # 未实现盈亏
    unrealized_pnl_pct: float # 未实现盈亏率
```

### StrategySignal (策略信号)
```python
@dataclass
class StrategySignal:
    signal_id: str           # 信号ID
    strategy_id: int         # 策略ID
    stock_code: str          # 股票代码
    action: str              # 操作类型 (buy/sell/hold)
    quantity: int            # 数量
    confidence: float        # 置信度 (0.0-1.0)
    timestamp: datetime      # 时间戳
```

## 🔧 使用方法

### 1. 启动服务
```python
# 服务会自动启动，无需手动初始化
from services.enhanced_trading_service import enhanced_trading_service
from services.strategy_executor import strategy_executor
from services.market_data_service import market_data_service
```

### 2. 基本交易操作
```python
# 下单
order_result = await enhanced_trading_service.place_order(
    user_id=1,
    stock_code="000001.XSHE",
    order_type="market",
    quantity=100,
    order_side="buy"
)

# 获取持仓
positions = await enhanced_trading_service.get_positions()

# 获取投资组合
portfolio = await enhanced_trading_service.get_portfolio()
```

### 3. 策略信号执行
```python
# 创建策略信号
signal = StrategySignal(
    signal_id="signal_001",
    strategy_id=1,
    stock_code="000001.XSHE",
    action="buy",
    quantity=500,
    confidence=0.8,
    timestamp=datetime.now()
)

# 添加到执行队列
await strategy_executor.add_signal(signal)
```

### 4. 实时行情订阅
```python
# 获取股票行情
quote = await market_data_service.get_stock_quote("000001.XSHE")

# 获取市场概览
overview = await market_data_service.get_market_overview()

# 批量获取行情
quotes = await market_data_service.get_multiple_quotes(["000001.XSHE", "000002.XSHE"])
```

## 📈 性能特性

### 异步处理
- 所有核心操作都支持异步处理
- 非阻塞的I/O操作
- 高并发处理能力

### 智能缓存
- 行情数据智能缓存
- 减少重复API调用
- 提升响应速度

### 批量操作
- 支持批量获取行情
- 批量更新持仓
- 优化网络请求

## 🛡️ 风险控制

### 风险限制
- **单只股票最大仓位**: 20%
- **日最大亏损**: 5%
- **最大回撤**: 15%
- **止损**: 8%
- **止盈**: 20%

### 风险检查
- 下单前自动风险验证
- 实时风险指标计算
- 风险预警自动触发
- 动态风险参数调整

## 🔍 监控和日志

### 执行状态监控
```python
# 获取策略执行状态
status = await strategy_executor.get_execution_status()
print(f"队列大小: {status['queue_size']}")
print(f"活跃策略: {status['active_strategies']}")
print(f"执行历史: {status['execution_history_count']}")
```

### 风险指标监控
```python
# 获取风险指标
risk_metrics = await enhanced_trading_service.get_risk_metrics()
print(f"风险等级: {risk_metrics['risk_level']}")
print(f"最大回撤: {risk_metrics['max_drawdown']:.2%}")
print(f"夏普比率: {risk_metrics['sharpe_ratio']:.2f}")
```

## 🧪 测试

### 运行测试
```bash
# 测试核心交易引擎
python test_core_trading_engine.py
```

### 测试覆盖
- 增强版交易服务功能测试
- 策略执行引擎功能测试
- 实时行情服务功能测试
- 集成功能测试

## 📝 配置说明

### 风险参数配置
```python
# 在 enhanced_trading_service.py 中修改
self.risk_limits = {
    "max_position_size": 0.2,      # 单只股票最大仓位
    "max_daily_loss": 0.05,        # 日最大亏损
    "max_drawdown": 0.15,          # 最大回撤
    "stop_loss": 0.08,             # 止损
    "take_profit": 0.20            # 止盈
}
```

### 更新频率配置
```python
# 在 market_data_service.py 中修改
self.update_interval = 5  # 5秒更新一次行情
```

## 🚨 注意事项

### 1. 数据源依赖
- 核心功能依赖聚宽数据源
- 确保聚宽账号配置正确
- 注意API调用频率限制

### 2. 风险控制
- 系统提供基础风险控制
- 建议根据实际情况调整风险参数
- 重要交易建议人工复核

### 3. 性能考虑
- 大量股票订阅可能影响性能
- 建议合理设置更新频率
- 监控系统资源使用情况

## 🔮 未来扩展

### 计划功能
- [ ] 更多策略类型支持
- [ ] 机器学习策略集成
- [ ] 高级风险模型
- [ ] 多账户管理
- [ ] 实时通知系统

### 技术优化
- [ ] Redis缓存集成
- [ ] 数据库持久化
- [ ] 微服务架构优化
- [ ] 性能监控增强

## 📞 技术支持

如有问题或建议，请：
1. 查看日志文件获取详细错误信息
2. 检查配置文件是否正确
3. 验证聚宽数据源连接状态
4. 运行测试脚本验证功能

---

**版本**: v2.0.0  
**更新日期**: 2025-01-27  
**作者**: liudong-work
