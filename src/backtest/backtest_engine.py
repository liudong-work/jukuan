"""
回测引擎
实现策略回测的核心功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from ..strategies.base_strategy import BaseStrategy

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 1000000):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        
        # 回测参数
        self.start_date = None
        self.end_date = None
        
        # 回测结果
        self.backtest_results = {}
        self.trade_log = []
        self.equity_curve = []
        
        logging.info(f"回测引擎初始化完成，初始资金: {initial_capital}")
    
    def run_backtest(self, 
                     strategy: BaseStrategy,
                     data: pd.DataFrame,
                     start_date: str = None,
                     end_date: str = None) -> Dict:
        """
        运行回测
        
        Args:
            strategy: 交易策略
            data: 市场数据
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict: 回测结果
        """
        logging.info(f"开始运行回测: {strategy.name}")
        
        # 设置回测时间范围
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        if data.empty:
            logging.error("回测数据为空")
            return {}
        
        # 重置策略和投资组合
        strategy.reset()
        self._reset_portfolio()
        
        # 生成交易信号
        signal_data = strategy.generate_signals(data)
        
        # 执行回测
        self._execute_backtest(strategy, signal_data)
        
        # 分析性能
        results = self._analyze_results(strategy)
        
        logging.info(f"回测完成: {strategy.name}")
        return results
    
    def _reset_portfolio(self):
        """重置投资组合"""
        self.cash = self.initial_capital
        self.positions = {}
        self.trade_log = []
        self.equity_curve = []
    
    def _execute_backtest(self, strategy: BaseStrategy, data: pd.DataFrame):
        """执行回测逻辑"""
        for timestamp, row in data.iterrows():
            if pd.isna(row['signal']) or row['signal'] == 0:
                continue
            
            # 获取当前价格
            current_price = row['close']
            
            # 计算交易数量
            quantity = strategy.calculate_position_size(
                row['signal'], current_price, self.cash
            )
            
            if quantity > 0:
                # 执行交易
                success = self._execute_trade(
                    'current_security', row['signal'], current_price, quantity, timestamp
                )
                
                if success:
                    # 更新权益曲线
                    self._update_equity_curve(timestamp, current_price)
    
    def _execute_trade(self, security: str, signal: int, price: float, 
                       quantity: int, timestamp: datetime) -> bool:
        """执行交易"""
        try:
            # 记录交易
            trade = {
                'timestamp': timestamp,
                'security': security,
                'signal': signal,
                'price': price,
                'quantity': quantity,
                'value': price * quantity
            }
            
            # 更新持仓
            if security not in self.positions:
                self.positions[security] = 0
            
            self.positions[security] += quantity * signal
            
            # 更新现金
            self.cash -= price * quantity * signal
            
            # 记录交易
            self.trade_log.append(trade)
            
            logging.info(f"执行交易: {security} {signal} {quantity} @ {price}")
            return True
            
        except Exception as e:
            logging.error(f"执行交易失败: {e}")
            return False
    
    def _update_equity_curve(self, timestamp: datetime, price: float):
        """更新权益曲线"""
        # 计算当前总资产
        total_value = self.cash
        for sec, pos in self.positions.items():
            if pos != 0:
                total_value += pos * price
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': total_value,
            'cash': self.cash
        })
    
    def _analyze_results(self, strategy: BaseStrategy) -> Dict:
        """分析回测结果"""
        # 获取策略性能指标
        strategy_metrics = strategy.get_performance_metrics()
        
        # 计算投资组合性能
        portfolio_metrics = self._calculate_portfolio_metrics()
        
        # 合并结果
        results = {
            'strategy_name': strategy.name,
            'strategy_metrics': strategy_metrics,
            'portfolio_metrics': portfolio_metrics,
            'trade_summary': {
                'total_trades': len(self.trade_log),
                'buy_trades': len([t for t in self.trade_log if t['signal'] == 1]),
                'sell_trades': len([t for t in self.trade_log if t['signal'] == -1])
            },
            'equity_curve': self.equity_curve,
            'trade_log': self.trade_log
        }
        
        self.backtest_results = results
        return results
    
    def _calculate_portfolio_metrics(self) -> Dict:
        """计算投资组合性能指标"""
        if not self.equity_curve:
            return {}
        
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('timestamp', inplace=True)
        
        # 计算收益率
        equity_df['returns'] = equity_df['equity'].pct_change()
        
        # 计算性能指标
        total_return = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0]) - 1
        annual_return = total_return * (252 / len(equity_df))
        volatility = equity_df['returns'].std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # 最大回撤
        equity_df['cummax'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax']
        max_drawdown = equity_df['drawdown'].min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'final_value': equity_df['equity'].iloc[-1]
        }
    
    def get_backtest_summary(self) -> Dict:
        """获取回测摘要"""
        if not self.backtest_results:
            return {}
        
        strategy_metrics = self.backtest_results['strategy_metrics']
        portfolio_metrics = self.backtest_results['portfolio_metrics']
        
        summary = {
            '策略名称': self.backtest_results['strategy_name'],
            '总收益率': f"{strategy_metrics.get('total_return', 0):.2%}",
            '年化收益率': f"{strategy_metrics.get('annual_return', 0):.2%}",
            '夏普比率': f"{strategy_metrics.get('sharpe_ratio', 0):.2f}",
            '最大回撤': f"{strategy_metrics.get('max_drawdown', 0):.2%}",
            '总交易次数': self.backtest_results['trade_summary']['total_trades'],
            '最终资产': f"{portfolio_metrics.get('final_value', 0):,.0f}"
        }
        
        return summary
    
    def plot_results(self, save_path: str = None):
        """绘制回测结果图表"""
        if not self.backtest_results:
            logging.warning("没有回测结果可供绘制")
            return
        
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # 设置样式
            plt.style.use('seaborn-v0_8')
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # 权益曲线
            equity_df = pd.DataFrame(self.backtest_results['equity_curve'])
            if not equity_df.empty:
                equity_df.set_index('timestamp', inplace=True)
                axes[0, 0].plot(equity_df.index, equity_df['equity'])
                axes[0, 0].set_title('权益曲线')
                axes[0, 0].set_ylabel('资产价值')
                axes[0, 0].grid(True)
            
            # 收益率分布
            if 'strategy_metrics' in self.backtest_results:
                returns = pd.Series(self.backtest_results['equity_curve'])
                if len(returns) > 1:
                    returns = returns.pct_change().dropna()
                    axes[0, 1].hist(returns, bins=30, alpha=0.7)
                    axes[0, 1].set_title('收益率分布')
                    axes[0, 1].set_xlabel('收益率')
                    axes[0, 1].set_ylabel('频次')
            
            # 回撤曲线
            if 'strategy_metrics' in self.backtest_results:
                equity_df = pd.DataFrame(self.backtest_results['equity_curve'])
                if not equity_df.empty:
                    equity_df.set_index('timestamp', inplace=True)
                    equity_df['cummax'] = equity_df['equity'].cummax()
                    equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax']
                    axes[1, 0].fill_between(equity_df.index, equity_df['drawdown'], 0, alpha=0.3, color='red')
                    axes[1, 0].set_title('回撤曲线')
                    axes[1, 0].set_ylabel('回撤')
                    axes[1, 0].grid(True)
            
            # 交易统计
            trade_summary = self.backtest_results['trade_summary']
            labels = ['买入', '卖出']
            sizes = [trade_summary['buy_trades'], trade_summary['sell_trades']]
            axes[1, 1].pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            axes[1, 1].set_title('交易分布')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logging.info(f"图表已保存到: {save_path}")
            
            plt.show()
            
        except ImportError:
            logging.error("matplotlib未安装，无法绘制图表")
        except Exception as e:
            logging.error(f"绘制图表失败: {e}")
    
    def export_results(self, file_path: str):
        """导出回测结果"""
        if not self.backtest_results:
            logging.warning("没有回测结果可供导出")
            return
        
        try:
            # 导出权益曲线
            equity_df = pd.DataFrame(self.backtest_results['equity_curve'])
            if not equity_df.empty:
                equity_df.to_csv(f"{file_path}_equity_curve.csv", index=False)
            
            # 导出交易记录
            trade_df = pd.DataFrame(self.backtest_results['trade_log'])
            if not trade_df.empty:
                trade_df.to_csv(f"{file_path}_trades.csv", index=False)
            
            # 导出性能指标
            summary_df = pd.DataFrame([self.get_backtest_summary()])
            summary_df.to_csv(f"{file_path}_summary.csv", index=False)
            
            logging.info(f"回测结果已导出到: {file_path}")
            
        except Exception as e:
            logging.error(f"导出结果失败: {e}")
