"""
高频数据挖掘策略
充分利用有限数据范围，通过高频采样和算法优化获取更多信息
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging

class HighFrequencyDataMiner:
    """高频数据挖掘器"""
    
    def __init__(self, data_provider):
        self.data_provider = data_provider
        self.logger = logging.getLogger(__name__)
        
        # 高频策略配置
        self.config = {
            'ma_periods': [3, 5, 8, 13, 21],  # 多周期均线
            'rsi_periods': [5, 7, 10, 14],    # 多周期RSI
            'volume_periods': [3, 5, 10, 20], # 多周期成交量
            'momentum_windows': [1, 3, 5, 10] # 多窗口动量
        }
    
    def mine_comprehensive_data(self, stock_code: str) -> Dict:
        """综合数据挖掘 - 从一只股票中提取最大信息量"""
        try:
            # 获取基础日线数据
            end_date = '2025-05-14'
            start_date = '2024-05-07'
            
            daily_data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
            
            if daily_data.empty or len(daily_data) < 20:
                return {}
            
            # 数据增强处理
            enhanced_data = self._enhance_daily_data(daily_data)
            
            # 多维度指标计算
            indicators = self._calculate_multi_dimension_indicators(enhanced_data)
            
            # 模式识别
            patterns = self._identify_patterns(enhanced_data, indicators)
            
            # 信号生成
            signals = self._generate_signals(enhanced_data, indicators, patterns)
            
            return {
                'stock_code': stock_code,
                'data_points': len(daily_data),
                'date_range': f"{start_date} 至 {end_date}",
                'enhanced_data': enhanced_data,
                'indicators': indicators,
                'patterns': patterns,
                'signals': signals
            }
            
        except Exception as e:
            self.logger.error(f"数据挖掘失败 {stock_code}: {e}")
            return {}
    
    def _enhance_daily_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """增强日线数据"""
        enhanced = data.copy()
        
        # 价格分层分析
        enhanced['price_level'] = pd.cut(enhanced['close'], bins=10, labels=False)
        enhanced['price_zone'] = pd.cut(enhanced['close'], bins=5, labels=['极低', '低', '中', '高', '极高'])
        
        # 成交量分析
        enhanced['volume_ma3'] = enhanced['volume'].rolling(3).mean()
        enhanced['volume_ma5'] = enhanced['volume'].rolling(5).mean()
        enhanced['volume_ma10'] = enhanced['volume'].rolling(10).mean()
        enhanced['volume_ratio'] = enhanced['volume'] / enhanced['volume_ma5']
        enhanced['volume_trend'] = enhanced['volume'].pct_change()
        
        # 价格波动分析
        enhanced['price_range'] = enhanced['high'] - enhanced['low']
        enhanced['price_range_ratio'] = enhanced['price_range'] / enhanced['close']
        enhanced['price_efficiency'] = abs(enhanced['close'] - enhanced['open']) / enhanced['price_range']
        
        # 多周期均线
        for period in self.config['ma_periods']:
            enhanced[f'MA_{period}'] = enhanced['close'].rolling(period).mean()
            enhanced[f'MA_{period}_slope'] = enhanced[f'MA_{period}'].pct_change()
        
        # 多周期RSI
        for period in self.config['rsi_periods']:
            enhanced[f'RSI_{period}'] = self._calculate_rsi(enhanced['close'], period)
        
        # 动量指标
        for window in self.config['momentum_windows']:
            enhanced[f'momentum_{window}'] = enhanced['close'].pct_change(window)
            enhanced[f'momentum_ma_{window}'] = enhanced[f'momentum_{window}'].rolling(3).mean()
        
        return enhanced
    
    def _calculate_multi_dimension_indicators(self, data: pd.DataFrame) -> Dict:
        """计算多维度技术指标"""
        indicators = {}
        
        # 趋势指标
        indicators['trend'] = {
            'ma_alignment': self._check_ma_alignment(data),
            'trend_strength': self._calculate_trend_strength(data)
        }
        
        # 动量指标
        indicators['momentum'] = {
            'rsi_momentum': self._calculate_rsi_momentum(data),
            'price_momentum': self._calculate_price_momentum(data)
        }
        
        # 波动率指标
        indicators['volatility'] = {
            'price_volatility': self._calculate_price_volatility(data),
            'volatility_regime': self._identify_volatility_regime(data)
        }
        
        return indicators
    
    def _calculate_price_momentum(self, data: pd.DataFrame) -> Dict:
        """计算价格动量"""
        momentum_windows = self.config['momentum_windows']
        momentum = {}
        
        for window in momentum_windows:
            col = f'momentum_{window}'
            if col in data.columns:
                latest = data[col].iloc[-1]
                momentum[f'{window}日动量'] = {
                    'value': latest,
                    'trend': '上升' if latest > 0 else '下降',
                    'strength': abs(latest)
                }
        
        return momentum
    
    def _calculate_price_volatility(self, data: pd.DataFrame) -> float:
        """计算价格波动率"""
        if len(data) < 20:
            return 0.0
        
        returns = data['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100
        
        return volatility
    
    def _identify_volatility_regime(self, data: pd.DataFrame) -> str:
        """识别波动率状态"""
        volatility = self._calculate_price_volatility(data)
        
        if volatility < 15:
            return '低波动'
        elif volatility < 25:
            return '中波动'
        else:
            return '高波动'
    
    def _check_ma_alignment(self, data: pd.DataFrame) -> Dict:
        """检查均线排列"""
        ma_periods = self.config['ma_periods']
        latest = data.iloc[-1]
        
        alignment = {}
        for period in ma_periods:
            ma_col = f'MA_{period}'
            if ma_col in latest:
                alignment[f'MA_{period}'] = latest[ma_col]
        
        # 判断均线排列类型
        ma_values = list(alignment.values())
        if len(ma_values) >= 3:
            if ma_values[0] > ma_values[1] > ma_values[2]:
                alignment['type'] = '多头排列'
                alignment['strength'] = '强'
            elif ma_values[0] < ma_values[1] < ma_values[2]:
                alignment['type'] = '空头排列'
                alignment['strength'] = '强'
            else:
                alignment['type'] = '混乱排列'
                alignment['strength'] = '弱'
        
        return alignment
    
    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """计算趋势强度"""
        if len(data) < 20:
            return 0.0
        
        x = np.arange(len(data))
        y = data['close'].values
        slope = np.polyfit(x, y, 1)[0]
        trend_strength = abs(slope) / np.mean(y) * 100
        
        return trend_strength
    
    def _calculate_rsi_momentum(self, data: pd.DataFrame) -> Dict:
        """计算RSI动量"""
        rsi_periods = self.config['rsi_periods']
        momentum = {}
        
        for period in rsi_periods:
            rsi_col = f'RSI_{period}'
            if rsi_col in data.columns:
                latest_rsi = data[rsi_col].iloc[-1]
                prev_rsi = data[rsi_col].iloc[-2] if len(data) > 1 else latest_rsi
                
                momentum[f'RSI_{period}'] = {
                    'current': latest_rsi,
                    'change': latest_rsi - prev_rsi,
                    'trend': '上升' if latest_rsi > prev_rsi else '下降',
                    'level': self._classify_rsi_level(latest_rsi)
                }
        
        return momentum
    
    def _classify_rsi_level(self, rsi: float) -> str:
        """分类RSI水平"""
        if rsi < 20:
            return '极超卖'
        elif rsi < 30:
            return '超卖'
        elif rsi < 40:
            return '偏弱'
        elif rsi < 60:
            return '中性'
        elif rsi < 70:
            return '偏强'
        elif rsi < 80:
            return '超买'
        else:
            return '极超买'
    
    def _identify_patterns(self, data: pd.DataFrame, indicators: Dict) -> Dict:
        """识别价格和成交量模式"""
        patterns = {}
        patterns['price'] = self._identify_price_patterns(data)
        patterns['volume'] = self._identify_volume_patterns(data)
        return patterns
    
    def _identify_price_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """识别价格模式"""
        patterns = []
        
        if len(data) < 5:
            return patterns
        
        # 双底模式
        if self._is_double_bottom(data):
            patterns.append({
                'type': '双底',
                'confidence': '高',
                'description': '价格在相近水平形成两个低点'
            })
        
        return patterns
    
    def _is_double_bottom(self, data: pd.DataFrame) -> bool:
        """判断是否形成双底"""
        if len(data) < 10:
            return False
        
        lows = data['low'].rolling(3).min()
        recent_lows = lows.tail(10)
        min_low = recent_lows.min()
        low_points = recent_lows[recent_lows <= min_low * 1.02]
        
        return len(low_points) >= 2
    
    def _identify_volume_patterns(self, data: pd.DataFrame) -> List[str]:
        """识别成交量模式"""
        patterns = []
        
        if 'volume_ratio' not in data.columns:
            return patterns
        
        recent_volume = data['volume_ratio'].tail(5)
        
        if recent_volume.iloc[-1] > 2.0:
            patterns.append('放量突破')
        
        if recent_volume.iloc[-1] < 0.5:
            patterns.append('缩量整理')
        
        return patterns
    
    def _generate_signals(self, data: pd.DataFrame, indicators: Dict, patterns: Dict) -> List[Dict]:
        """生成交易信号"""
        signals = []
        
        # 趋势信号
        if indicators.get('trend', {}).get('ma_alignment', {}).get('type') == '多头排列':
            signals.append({
                'type': '趋势信号',
                'signal': '买入',
                'strength': '强',
                'reason': '均线多头排列，趋势向上',
                'confidence': 0.8
            })
        
        # RSI信号
        rsi_momentum = indicators.get('momentum', {}).get('rsi_momentum', {})
        for period, rsi_data in rsi_momentum.items():
            if rsi_data.get('level') in ['超卖', '极超卖'] and rsi_data.get('trend') == '上升':
                signals.append({
                    'type': 'RSI信号',
                    'signal': '买入',
                    'strength': '中',
                    'reason': f'{period} RSI超卖反弹',
                    'confidence': 0.7
                })
        
        return signals
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
