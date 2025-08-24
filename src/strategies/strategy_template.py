#!/usr/bin/env python3
"""
策略开发模板
复制此文件并修改以创建新策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from .base_strategy import BaseStrategy

class StrategyTemplate(BaseStrategy):
    """
    策略模板 - 请复制此文件并修改以创建新策略
    
    使用步骤：
    1. 复制此文件并重命名
    2. 修改类名和策略名称
    3. 实现你的指标计算逻辑
    4. 实现你的信号生成逻辑
    5. 调整参数和配置
    """
    
    def __init__(self, parameters: Dict = None):
        """
        初始化策略
        
        Args:
            parameters: 策略参数字典
        """
        # 设置默认参数 - 请根据你的策略需要修改
        default_params = {
            'param1': 10,        # 参数1描述
            'param2': 20,        # 参数2描述
            'param3': 0.1,       # 参数3描述
            'position_size': 0.1 # 仓位比例
        }
        
        # 合并用户提供的参数
        if parameters:
            default_params.update(parameters)
        
        # 调用父类初始化
        super().__init__("策略模板", default_params)
        
        # 提取参数到实例变量 - 请根据你的参数修改
        self.param1 = self.parameters['param1']
        self.param2 = self.parameters['param2']
        self.param3 = self.parameters['param3']
        self.position_size = self.parameters['position_size']
        
        logging.info(f"策略模板初始化完成，参数: {self.parameters}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            pd.DataFrame: 包含计算出的指标的数据
        """
        result = data.copy()
        
        # ===== 在这里实现你的指标计算逻辑 =====
        
        # 示例1：移动平均线
        result['MA5'] = result['close'].rolling(window=5).mean()
        result['MA20'] = result['close'].rolling(window=20).mean()
        
        # 示例2：RSI指标
        delta = result['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result['RSI'] = 100 - (100 / (1 + rs))
        
        # 示例3：布林带
        result['BB_MIDDLE'] = result['close'].rolling(window=20).mean()
        bb_std = result['close'].rolling(window=20).std()
        result['BB_UPPER'] = result['BB_MIDDLE'] + (bb_std * 2)
        result['BB_LOWER'] = result['BB_MIDDLE'] - (bb_std * 2)
        
        # ===== 添加你的自定义指标 =====
        
        return result
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            pd.DataFrame: 包含交易信号的数据
        """
        # 先计算指标
        result = self.calculate_indicators(data)
        
        # ===== 在这里实现你的信号生成逻辑 =====
        
        # 初始化信号列
        result['signal'] = 0  # 0=持有, 1=买入, -1=卖出
        
        # 示例1：双均线交叉策略
        result['ma_cross'] = np.where(
            (result['MA5'] > result['MA20']) & 
            (result['MA5'].shift(1) <= result['MA20'].shift(1)), 
            1,  # 金叉买入
            np.where(
                (result['MA5'] < result['MA20']) & 
                (result['MA5'].shift(1) >= result['MA20'].shift(1)), 
                -1,  # 死叉卖出
                0    # 无信号
            )
        )
        
        # 示例2：RSI超买超卖策略
        result['rsi_signal'] = np.where(
            result['RSI'] < 30, 1,    # RSI < 30 超卖买入
            np.where(
                result['RSI'] > 70, -1,  # RSI > 70 超买卖出
                0  # 无信号
            )
        )
        
        # 示例3：布林带突破策略
        result['bb_signal'] = np.where(
            result['close'] < result['BB_LOWER'], 1,    # 价格突破下轨买入
            np.where(
                result['close'] > result['BB_UPPER'], -1,  # 价格突破上轨卖出
                0  # 无信号
            )
        )
        
        # ===== 综合信号逻辑 =====
        # 你可以组合多个信号，或者使用加权平均
        # 这里使用简单的信号组合示例
        result['signal'] = result['ma_cross']  # 暂时只使用均线交叉信号
        
        # ===== 添加你的自定义信号逻辑 =====
        
        return result
    
    def calculate_position_size(self, signal: int, price: float, cash: float) -> int:
        """
        计算仓位大小
        
        Args:
            signal: 交易信号 (1=买入, -1=卖出, 0=持有)
            price: 当前价格
            cash: 可用资金
            
        Returns:
            int: 交易数量
        """
        if signal == 0:
            return 0
        
        # 根据信号和资金计算仓位
        position_value = cash * self.position_size
        
        # 计算可买入的股票数量
        quantity = int(position_value / price)
        
        # 返回正数（买入）或负数（卖出）
        return quantity if signal > 0 else -quantity
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """
        获取策略摘要信息
        
        Returns:
            Dict: 策略摘要
        """
        return {
            "name": self.name,
            "type": "custom",
            "parameters": self.parameters,
            "description": "基于技术指标的量化交易策略",
            "indicators": ["MA5", "MA20", "RSI", "BB_UPPER", "BB_MIDDLE", "BB_LOWER"],
            "signals": ["ma_cross", "rsi_signal", "bb_signal"]
        }
    
    def validate_parameters(self) -> bool:
        """
        验证策略参数
        
        Returns:
            bool: 参数是否有效
        """
        try:
            # 检查参数类型和范围
            if not isinstance(self.param1, (int, float)) or self.param1 <= 0:
                return False
            
            if not isinstance(self.param2, (int, float)) or self.param2 <= 0:
                return False
            
            if not isinstance(self.param3, (int, float)) or self.param3 <= 0 or self.param3 > 1:
                return False
            
            if not isinstance(self.position_size, (int, float)) or self.position_size <= 0 or self.position_size > 1:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"参数验证失败: {e}")
            return False
    
    def get_parameter_ranges(self) -> Dict[str, Dict[str, Any]]:
        """
        获取参数的有效范围
        
        Returns:
            Dict: 参数范围信息
        """
        return {
            "param1": {
                "min": 1,
                "max": 100,
                "step": 1,
                "description": "参数1描述"
            },
            "param2": {
                "min": 1,
                "max": 100,
                "step": 1,
                "description": "参数2描述"
            },
            "param3": {
                "min": 0.01,
                "max": 1.0,
                "step": 0.01,
                "description": "参数3描述"
            },
            "position_size": {
                "min": 0.01,
                "max": 1.0,
                "step": 0.01,
                "description": "仓位比例"
            }
        }


# ===== 使用示例 =====
if __name__ == "__main__":
    # 创建策略实例
    strategy = StrategyTemplate({
        'param1': 15,
        'param2': 25,
        'param3': 0.15,
        'position_size': 0.2
    })
    
    # 验证参数
    if strategy.validate_parameters():
        print("参数验证通过")
        print(f"策略摘要: {strategy.get_strategy_summary()}")
        print(f"参数范围: {strategy.get_parameter_ranges()}")
    else:
        print("参数验证失败")
