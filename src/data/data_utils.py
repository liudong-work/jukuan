"""
数据工具类
提供数据处理、清洗、分析等辅助功能
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

class DataUtils:
    """数据工具类"""
    
    @staticmethod
    def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            pd.DataFrame: 添加技术指标的DataFrame
        """
        if df.empty:
            return df
        
        result = df.copy()
        
        # 移动平均线
        result['MA5'] = result['close'].rolling(window=5).mean()
        result['MA10'] = result['close'].rolling(window=10).mean()
        result['MA20'] = result['close'].rolling(window=20).mean()
        result['MA60'] = result['close'].rolling(window=60).mean()
        
        # 指数移动平均线
        result['EMA12'] = result['close'].ewm(span=12).mean()
        result['EMA26'] = result['close'].ewm(span=26).mean()
        
        # MACD
        result['MACD'] = result['EMA12'] - result['EMA26']
        result['MACD_Signal'] = result['MACD'].ewm(span=9).mean()
        result['MACD_Histogram'] = result['MACD'] - result['MACD_Signal']
        
        # RSI
        delta = result['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result['RSI'] = 100 - (100 / (1 + rs))
        
        # 布林带
        result['BB_Middle'] = result['close'].rolling(window=20).mean()
        bb_std = result['close'].rolling(window=20).std()
        result['BB_Upper'] = result['BB_Middle'] + (bb_std * 2)
        result['BB_Lower'] = result['BB_Middle'] - (bb_std * 2)
        
        # KDJ
        low_min = result['low'].rolling(window=9).min()
        high_max = result['high'].rolling(window=9).max()
        result['K'] = 100 * ((result['close'] - low_min) / (high_max - low_min))
        result['D'] = result['K'].rolling(window=3).mean()
        result['J'] = 3 * result['K'] - 2 * result['D']
        
        # 成交量指标
        result['Volume_MA5'] = result['volume'].rolling(window=5).mean()
        result['Volume_MA10'] = result['volume'].rolling(window=10).mean()
        
        return result
    
    @staticmethod
    def calculate_returns(df: pd.DataFrame, method: str = 'log') -> pd.DataFrame:
        """
        计算收益率
        
        Args:
            df: 价格数据DataFrame
            method: 计算方法 ('log'=对数收益率, 'simple'=简单收益率)
            
        Returns:
            pd.DataFrame: 包含收益率的DataFrame
        """
        if df.empty:
            return df
        
        result = df.copy()
        
        if method == 'log':
            result['returns'] = np.log(result['close'] / result['close'].shift(1))
        elif method == 'simple':
            result['returns'] = (result['close'] - result['close'].shift(1)) / result['close'].shift(1)
        else:
            logging.error(f"不支持的收益率计算方法: {method}")
            return df
        
        return result
    
    @staticmethod
    def calculate_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        计算波动率
        
        Args:
            df: 收益率数据DataFrame
            window: 计算窗口
            
        Returns:
            pd.DataFrame: 包含波动率的DataFrame
        """
        if df.empty or 'returns' not in df.columns:
            logging.error("DataFrame必须包含returns列")
            return df
        
        result = df.copy()
        
        # 滚动波动率
        result['volatility'] = result['returns'].rolling(window=window).std() * np.sqrt(252)
        
        # 历史波动率
        result['historical_volatility'] = result['returns'].expanding().std() * np.sqrt(252)
        
        return result
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame, column: str, method: str = 'iqr') -> pd.DataFrame:
        """
        检测异常值
        
        Args:
            df: 数据DataFrame
            column: 检测列名
            method: 检测方法 ('iqr'=四分位距, 'zscore'=Z分数)
            
        Returns:
            pd.DataFrame: 标记异常值的DataFrame
        """
        if df.empty or column not in df.columns:
            logging.error(f"列 {column} 不存在")
            return df
        
        result = df.copy()
        
        if method == 'iqr':
            Q1 = result[column].quantile(0.25)
            Q3 = result[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            result['is_outlier'] = (result[column] < lower_bound) | (result[column] > upper_bound)
            
        elif method == 'zscore':
            z_scores = np.abs((result[column] - result[column].mean()) / result[column].std())
            result['is_outlier'] = z_scores > 3
            
        else:
            logging.error(f"不支持的异常值检测方法: {method}")
            return df
        
        return result
    
    @staticmethod
    def resample_data(df: pd.DataFrame, freq: str) -> pd.DataFrame:
        """
        重采样数据
        
        Args:
            df: 原始数据DataFrame
            freq: 目标频率 ('D'=日, 'W'=周, 'M'=月, 'Q'=季度, 'Y'=年)
            
        Returns:
            pd.DataFrame: 重采样后的数据
        """
        if df.empty:
            return df
        
        try:
            # 确保索引是时间类型
            if not isinstance(df.index, pd.DatetimeIndex):
                df = df.copy()
                df.index = pd.to_datetime(df.index)
            
            # 重采样
            resampled = df.resample(freq).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })
            
            return resampled.dropna()
            
        except Exception as e:
            logging.error(f"重采样失败: {e}")
            return df
    
    @staticmethod
    def normalize_data(df: pd.DataFrame, method: str = 'minmax') -> pd.DataFrame:
        """
        数据标准化
        
        Args:
            df: 原始数据DataFrame
            method: 标准化方法 ('minmax'=最小最大, 'zscore'=Z分数)
            
        Returns:
            pd.DataFrame: 标准化后的数据
        """
        if df.empty:
            return df
        
        result = df.copy()
        
        numeric_columns = result.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if method == 'minmax':
                min_val = result[col].min()
                max_val = result[col].max()
                if max_val != min_val:
                    result[col] = (result[col] - min_val) / (max_val - min_val)
                    
            elif method == 'zscore':
                mean_val = result[col].mean()
                std_val = result[col].std()
                if std_val != 0:
                    result[col] = (result[col] - mean_val) / std_val
                    
            else:
                logging.error(f"不支持的标准化方法: {method}")
                return df
        
        return result
    
    @staticmethod
    def calculate_correlation_matrix(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
        """
        计算相关性矩阵
        
        Args:
            df: 数据DataFrame
            columns: 计算相关性的列名列表
            
        Returns:
            pd.DataFrame: 相关性矩阵
        """
        if df.empty:
            return pd.DataFrame()
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # 过滤存在的列
        existing_columns = [col for col in columns if col in df.columns]
        
        if len(existing_columns) < 2:
            logging.error("至少需要2个数值列来计算相关性")
            return pd.DataFrame()
        
        correlation_matrix = df[existing_columns].corr()
        return correlation_matrix
    
    @staticmethod
    def calculate_rolling_statistics(df: pd.DataFrame, 
                                   column: str, 
                                   window: int = 20,
                                   statistics: List[str] = None) -> pd.DataFrame:
        """
        计算滚动统计量
        
        Args:
            df: 数据DataFrame
            column: 计算列名
            window: 滚动窗口大小
            statistics: 统计量列表
            
        Returns:
            pd.DataFrame: 包含滚动统计量的DataFrame
        """
        if df.empty or column not in df.columns:
            logging.error(f"列 {column} 不存在")
            return df
        
        if statistics is None:
            statistics = ['mean', 'std', 'min', 'max', 'median']
        
        result = df.copy()
        
        for stat in statistics:
            if stat == 'mean':
                result[f'{column}_{stat}_{window}'] = result[column].rolling(window=window).mean()
            elif stat == 'std':
                result[f'{column}_{stat}_{window}'] = result[column].rolling(window=window).std()
            elif stat == 'min':
                result[f'{column}_{stat}_{window}'] = result[column].rolling(window=window).min()
            elif stat == 'max':
                result[f'{column}_{stat}_{window}'] = result[column].rolling(window=window).max()
            elif stat == 'median':
                result[f'{column}_{stat}_{window}'] = result[column].rolling(window=window).median()
        
        return result
