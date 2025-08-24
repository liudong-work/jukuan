# 🚀 量化交易策略创建完整指南

## 📋 目录
1. [策略创建概述](#策略创建概述)
2. [快速开始](#快速开始)
3. [策略开发详细步骤](#策略开发详细步骤)
4. [策略类型和示例](#策略类型和示例)
5. [测试和验证](#测试和验证)
6. [部署和集成](#部署和集成)
7. [常见问题和解决方案](#常见问题和解决方案)

## 🎯 策略创建概述

在这个量化交易系统中，创建新策略需要完成以下几个步骤：

1. **策略代码实现** - 编写策略逻辑
2. **策略配置管理** - 添加到配置文件
3. **API端点集成** - 创建后端接口
4. **前端界面集成** - 更新用户界面
5. **测试和验证** - 确保策略正常工作

## ⚡ 快速开始

### 方法1：使用策略模板（推荐）

```bash
# 1. 复制策略模板
cp src/strategies/strategy_template.py src/strategies/my_strategy.py

# 2. 修改策略模板
# 3. 添加到配置文件
# 4. 测试策略
```

### 方法2：从头创建

```bash
# 1. 创建新策略文件
touch src/strategies/my_strategy.py

# 2. 实现策略逻辑
# 3. 添加到配置文件
# 4. 创建API端点
# 5. 更新前端界面
```

## 🔧 策略开发详细步骤

### 步骤1：创建策略类文件

在 `src/strategies/` 目录下创建新的策略文件，例如 `my_strategy.py`：

```python
#!/usr/bin/env python3
"""
我的策略
策略描述：基于XXX指标的XXX策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging
from .base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    """我的策略"""
    
    def __init__(self, parameters: Dict = None):
        # 设置默认参数
        default_params = {
            'param1': 10,
            'param2': 20,
            'param3': 0.1
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("我的策略", default_params)
        
        # 提取参数
        self.param1 = self.parameters['param1']
        self.param2 = self.parameters['param2']
        self.param3 = self.parameters['param3']
        
        logging.info(f"我的策略初始化完成，参数: {self.parameters}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        result = data.copy()
        
        # 在这里实现你的指标计算逻辑
        # 例如：移动平均线、RSI、布林带等
        
        return result
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        result = self.calculate_indicators(data)
        
        # 在这里实现你的信号生成逻辑
        # 返回包含信号列的DataFrame
        
        return result
    
    def calculate_position_size(self, signal: int, price: float, cash: float) -> int:
        """计算仓位大小"""
        if signal == 0:
            return 0
        
        # 根据信号和资金计算仓位
        position_value = cash * self.param3
        quantity = int(position_value / price)
        
        return quantity if signal > 0 else -quantity
```

### 步骤2：添加到策略配置文件

在 `data/strategies.json` 中添加新策略：

```json
{
  "id": 4,
  "name": "我的策略",
  "description": "基于XXX指标的XXX策略",
  "type": "custom",
  "status": "inactive",
  "parameters": {
    "param1": 10,
    "param2": 20,
    "param3": 0.1
  },
  "filters": {
    "custom_filter1": true,
    "custom_filter2": false
  },
  "created_at": "2025-08-21T00:00:00Z",
  "updated_at": "2025-08-21T00:00:00Z"
}
```

### 步骤3：创建策略API端点

在 `api/v1/endpoints/strategy.py` 中添加新端点：

```python
@router.post("/my-strategy")
async def run_my_strategy(
    request: Request,
    parameters: Optional[Dict[str, Any]] = None
):
    """运行我的策略"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )

        # 使用默认参数或请求参数
        if parameters is None:
            parameters = {
                'param1': 10,
                'param2': 20,
                'param3': 0.1
            }

        logger.info(f"开始运行我的策略，参数: {parameters}")

        # 这里调用实际的策略逻辑
        # 目前返回模拟结果
        strategy_results = {
            "strategy_name": "我的策略",
            "run_time": datetime.now().isoformat(),
            "parameters": parameters,
            "signals": [
                {
                    "code": "000001",
                    "name": "平安银行",
                    "signal": "buy",
                    "strength": 0.8,
                    "price": 12.85
                }
            ],
            "total_signals": 1
        }

        return {
            "success": True,
            "data": strategy_results,
            "message": "我的策略运行成功"
        }

    except Exception as e:
        logger.error(f"运行我的策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"运行我的策略失败: {str(e)}"
        )
```

### 步骤4：更新前端界面

在 `templates/strategy.html` 中添加新策略的UI元素：

```html
<!-- 在策略类型选择中添加 -->
<option value="custom">自定义策略</option>

<!-- 在策略参数配置中添加 -->
<div class="mb-3" id="custom-strategy-params" style="display: none;">
    <label class="form-label">自定义策略参数</label>
    <div class="row">
        <div class="col-md-4">
            <label class="form-label">参数1</label>
            <input type="number" class="form-control" id="param1" value="10">
        </div>
        <div class="col-md-4">
            <label class="form-label">参数2</label>
            <input type="number" class="form-control" id="param2" value="20">
        </div>
        <div class="col-md-4">
            <label class="form-label">参数3</label>
            <input type="number" class="form-control" id="param3" value="0.1" step="0.01">
        </div>
    </div>
</div>
```

## 📊 策略类型和示例

### 1. 趋势跟踪策略

```python
class TrendFollowingStrategy(BaseStrategy):
    """趋势跟踪策略"""
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        result = data.copy()
        
        # 计算移动平均线
        result['MA5'] = result['close'].rolling(window=5).mean()
        result['MA20'] = result['close'].rolling(window=20).mean()
        
        # 生成信号
        result['signal'] = np.where(
            result['MA5'] > result['MA20'], 1,  # 金叉买入
            np.where(
                result['MA5'] < result['MA20'], -1,  # 死叉卖出
                0  # 无信号
            )
        )
        
        return result
```

### 2. 均值回归策略

```python
class MeanReversionStrategy(BaseStrategy):
    """均值回归策略"""
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        result = data.copy()
        
        # 计算布林带
        result['BB_MIDDLE'] = result['close'].rolling(window=20).mean()
        bb_std = result['close'].rolling(window=20).std()
        result['BB_UPPER'] = result['BB_MIDDLE'] + (bb_std * 2)
        result['BB_LOWER'] = result['BB_MIDDLE'] - (bb_std * 2)
        
        # 生成信号
        result['signal'] = np.where(
            result['close'] < result['BB_LOWER'], 1,    # 价格突破下轨买入
            np.where(
                result['close'] > result['BB_UPPER'], -1,  # 价格突破上轨卖出
                0  # 无信号
            )
        )
        
        return result
```

### 3. 动量策略

```python
class MomentumStrategy(BaseStrategy):
    """动量策略"""
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        result = data.copy()
        
        # 计算动量指标
        result['momentum'] = result['close'].pct_change(periods=10)
        result['momentum_ma'] = result['momentum'].rolling(window=5).mean()
        
        # 生成信号
        result['signal'] = np.where(
            result['momentum_ma'] > 0.02, 1,    # 动量向上买入
            np.where(
                result['momentum_ma'] < -0.02, -1,  # 动量向下卖出
                0  # 无信号
            )
        )
        
        return result
```

## 🧪 测试和验证

### 创建测试脚本

```python
#!/usr/bin/env python3
"""
测试我的策略
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.strategies.my_strategy import MyStrategy
import pandas as pd
import numpy as np

def create_sample_data():
    """创建样本数据"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    data = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    return data

def test_my_strategy():
    """测试我的策略"""
    # 创建策略实例
    strategy = MyStrategy({
        'param1': 15,
        'param2': 25,
        'param3': 0.15
    })
    
    # 创建样本数据
    data = create_sample_data()
    
    # 生成信号
    signals = strategy.generate_signals(data)
    
    print("策略测试结果:")
    print(f"策略名称: {strategy.name}")
    print(f"参数: {strategy.parameters}")
    print(f"数据形状: {signals.shape}")
    print(f"信号列: {[col for col in signals.columns if 'signal' in col.lower()]}")
    
    return strategy, signals

if __name__ == "__main__":
    test_my_strategy()
```

### 运行测试

```bash
# 运行测试脚本
python test_my_strategy.py

# 或者直接测试
python -c "
from src.strategies.my_strategy import MyStrategy
strategy = MyStrategy()
print('策略创建成功:', strategy.name)
"
```

## 🚀 部署和集成

### 1. 重启应用

```bash
# 停止当前应用
pkill -f uvicorn

# 重新启动
python run_dev.py
```

### 2. 验证策略

1. 访问策略管理页面：`http://localhost:8000/strategy`
2. 检查新策略是否出现在列表中
3. 尝试运行策略
4. 检查策略状态和参数

### 3. 监控日志

```bash
# 查看应用日志
tail -f logs/app.log

# 或者查看控制台输出
```

## ❗ 常见问题和解决方案

### 问题1：策略导入失败

**错误信息**：`ModuleNotFoundError: No module named 'src.strategies.my_strategy'`

**解决方案**：
```python
# 确保在 __init__.py 中导入新策略
# src/strategies/__init__.py
from .my_strategy import MyStrategy

__all__ = ['MyStrategy', ...]
```

### 问题2：策略参数验证失败

**错误信息**：`参数验证失败`

**解决方案**：
```python
# 检查参数类型和范围
def validate_parameters(self) -> bool:
    try:
        if not isinstance(self.param1, (int, float)) or self.param1 <= 0:
            return False
        # ... 其他验证
        return True
    except Exception as e:
        logging.error(f"参数验证失败: {e}")
        return False
```

### 问题3：策略信号生成失败

**错误信息**：`生成信号失败`

**解决方案**：
```python
# 确保数据包含必要的列
def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    missing_columns = [col for col in required_columns if col not in data.columns]
    
    if missing_columns:
        raise ValueError(f"缺少必要的列: {missing_columns}")
    
    # ... 信号生成逻辑
```

### 问题4：前端显示异常

**错误信息**：`策略列表加载失败`

**解决方案**：
1. 检查浏览器控制台错误
2. 验证API端点是否正确
3. 检查策略数据格式

## 📚 进阶技巧

### 1. 策略组合

```python
class StrategyCombination:
    """策略组合"""
    
    def __init__(self, strategies: List[BaseStrategy], weights: List[float]):
        self.strategies = strategies
        self.weights = weights
    
    def generate_combined_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成组合信号"""
        combined_signals = pd.DataFrame()
        
        for i, strategy in enumerate(self.strategies):
            signals = strategy.generate_signals(data)
            combined_signals[f'strategy_{i}_signal'] = signals['signal'] * self.weights[i]
        
        # 计算加权平均信号
        combined_signals['combined_signal'] = combined_signals.sum(axis=1)
        
        return combined_signals
```

### 2. 动态参数优化

```python
class DynamicParameterOptimizer:
    """动态参数优化器"""
    
    def __init__(self, strategy_class, parameter_ranges):
        self.strategy_class = strategy_class
        self.parameter_ranges = parameter_ranges
    
    def optimize_parameters(self, data: pd.DataFrame, metric='sharpe_ratio'):
        """优化策略参数"""
        best_params = None
        best_metric = float('-inf')
        
        # 网格搜索最优参数
        for params in self.generate_parameter_combinations():
            strategy = self.strategy_class(params)
            signals = strategy.generate_signals(data)
            metric_value = self.calculate_metric(signals, metric)
            
            if metric_value > best_metric:
                best_metric = metric_value
                best_params = params
        
        return best_params, best_metric
```

### 3. 风险管理集成

```python
class RiskManager:
    """风险管理器"""
    
    def __init__(self, max_position_size: float = 0.1, stop_loss: float = 0.05):
        self.max_position_size = max_position_size
        self.stop_loss = stop_loss
    
    def adjust_position_size(self, signal: int, price: float, cash: float, 
                           current_positions: Dict) -> int:
        """调整仓位大小"""
        # 计算当前总仓位
        total_position_value = sum(abs(pos) * price for pos in current_positions.values())
        
        # 检查仓位限制
        if total_position_value / cash > self.max_position_size:
            return 0
        
        # 计算建议仓位
        suggested_position = int(cash * self.max_position_size / price)
        
        return min(suggested_position, abs(signal))
```

## 🎉 总结

创建新策略的完整流程：

1. **复制策略模板** - 使用 `strategy_template.py`
2. **修改策略逻辑** - 实现指标计算和信号生成
3. **添加配置** - 更新 `strategies.json`
4. **创建API端点** - 添加后端接口
5. **更新前端** - 修改用户界面
6. **测试验证** - 确保策略正常工作
7. **部署集成** - 重启应用并验证

记住：
- 继承 `BaseStrategy` 类
- 实现必要的方法：`generate_signals()`, `calculate_position_size()`
- 添加参数验证
- 创建测试脚本
- 监控日志和错误

祝你策略开发顺利！🚀
