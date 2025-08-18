"""
增强版交易服务模块
基于聚宽数据源的核心交易引擎
提供实时行情、策略执行、风险控制等功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
import json
import os
import numpy as np
from dataclasses import dataclass, asdict

# 导入聚宽服务
try:
    from .jq_service import jq_service
except ImportError:
    jq_service = None

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """市场数据结构"""
    stock_code: str
    current_price: float
    change: float
    change_pct: float
    volume: int
    amount: float
    high: float
    low: float
    open: float
    prev_close: float
    timestamp: datetime

@dataclass
class Position:
    """持仓数据结构"""
    stock_code: str
    stock_name: str
    quantity: int
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    created_at: datetime
    updated_at: datetime

@dataclass
class Order:
    """订单数据结构"""
    order_id: str
    user_id: int
    stock_code: str
    stock_name: str
    order_type: str  # market, limit
    order_side: str  # buy, sell
    quantity: int
    price: Optional[float]
    status: str  # pending, filled, cancelled, rejected
    filled_price: Optional[float]
    filled_quantity: int
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime]

@dataclass
class Portfolio:
    """投资组合数据结构"""
    user_id: int
    total_value: float
    cash: float
    positions_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    daily_pnl: float
    daily_pnl_pct: float
    created_at: datetime
    updated_at: datetime

class EnhancedTradingService:
    """增强版交易服务类"""
    
    def __init__(self):
        self.portfolio_file = "data/enhanced_portfolio.json"
        self.orders_file = "data/enhanced_orders.json"
        self.positions_file = "data/enhanced_positions.json"
        self.market_data_cache = {}
        self.risk_limits = {
            "max_position_size": 0.2,  # 单只股票最大仓位20%
            "max_daily_loss": 0.05,    # 日最大亏损5%
            "max_drawdown": 0.15,      # 最大回撤15%
            "stop_loss": 0.08,         # 止损8%
            "take_profit": 0.20        # 止盈20%
        }
        self._ensure_data_dir()
        
        # 启动实时行情更新
        if jq_service:
            asyncio.create_task(self._start_market_data_update())
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs("data", exist_ok=True)
        
        # 初始化默认数据文件
        if not os.path.exists(self.portfolio_file):
            self._init_default_portfolio()
        if not os.path.exists(self.orders_file):
            self._init_default_orders()
        if not os.path.exists(self.positions_file):
            self._init_default_positions()
    
    def _init_default_portfolio(self):
        """初始化默认投资组合"""
        default_portfolio = {
            "user_id": 1,
            "total_value": 1000000.0,
            "cash": 500000.0,
            "positions_value": 500000.0,
            "unrealized_pnl": 0.0,
            "unrealized_pnl_pct": 0.0,
            "daily_pnl": 0.0,
            "daily_pnl_pct": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self._save_data(self.portfolio_file, default_portfolio)
    
    def _init_default_orders(self):
        """初始化默认订单"""
        default_orders = {"orders": []}
        self._save_data(self.orders_file, default_orders)
    
    def _init_default_positions(self):
        """初始化默认持仓"""
        default_positions = {"positions": []}
        self._save_data(self.positions_file, default_positions)
    
    def _save_data(self, file_path: str, data: Any):
        """保存数据到文件"""
        try:
            # 处理datetime序列化
            if isinstance(data, dict):
                data = self._serialize_datetime(data)
            elif isinstance(data, list):
                data = [self._serialize_datetime(item) if isinstance(item, dict) else item for item in data]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存数据失败 {file_path}: {e}")
    
    def _serialize_datetime(self, obj: Any) -> Any:
        """序列化datetime对象"""
        if isinstance(obj, dict):
            return {k: self._serialize_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    def _load_data(self, file_path: str) -> Any:
        """从文件加载数据"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"加载数据失败 {file_path}: {e}")
            return None
    
    async def _start_market_data_update(self):
        """启动实时行情更新"""
        while True:
            try:
                await self._update_market_data()
                await asyncio.sleep(30)  # 每30秒更新一次
            except Exception as e:
                logger.error(f"更新市场数据失败: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟
    
    async def _update_market_data(self):
        """更新市场数据"""
        try:
            if not jq_service:
                return
            
            # 获取持仓股票的实时行情
            positions = await self.get_positions()
            if positions:
                stock_codes = [pos.stock_code for pos in positions]
                
                # 批量获取实时行情
                for stock_code in stock_codes:
                    try:
                        market_data = await self._get_stock_market_data(stock_code)
                        if market_data:
                            self.market_data_cache[stock_code] = market_data
                    except Exception as e:
                        logger.error(f"获取股票{stock_code}行情失败: {e}")
                
                # 更新持仓市值和盈亏
                await self._update_positions_value()
                
        except Exception as e:
            logger.error(f"更新市场数据失败: {e}")
    
    async def _get_stock_market_data(self, stock_code: str) -> Optional[MarketData]:
        """获取单个股票的市场数据"""
        try:
            if not jq_service:
                return None
            
            # 获取实时价格
            price_data = await jq_service._get_current_price(stock_code)
            if not price_data:
                return None
            
            # 获取日线数据计算涨跌幅
            end_date = datetime.now().strftime('%Y-%m-%d')
            daily_data = await jq_service.get_daily_data(stock_code, end_date, end_date)
            
            if daily_data and len(daily_data) > 0:
                today = daily_data[0]
                prev_close = today.get('close', 0)
                current_price = price_data.get('price', prev_close)
                change = current_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                
                return MarketData(
                    stock_code=stock_code,
                    current_price=current_price,
                    change=change,
                    change_pct=change_pct,
                    volume=today.get('volume', 0),
                    amount=today.get('amount', 0),
                    high=today.get('high', 0),
                    low=today.get('low', 0),
                    open=today.get('open', 0),
                    prev_close=prev_close,
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"获取股票{stock_code}市场数据失败: {e}")
            return None
    
    async def _update_positions_value(self):
        """更新持仓市值和盈亏"""
        try:
            positions_data = self._load_data(self.positions_file)
            if not positions_data or "positions" not in positions_data:
                return
            
            positions = positions_data["positions"]
            total_unrealized_pnl = 0.0
            
            for pos in positions:
                stock_code = pos["stock_code"]
                if stock_code in self.market_data_cache:
                    market_data = self.market_data_cache[stock_code]
                    current_price = market_data.current_price
                    quantity = pos["quantity"]
                    avg_price = pos["avg_price"]
                    
                    # 计算市值和盈亏
                    market_value = quantity * current_price
                    unrealized_pnl = (current_price - avg_price) * quantity
                    unrealized_pnl_pct = (unrealized_pnl / (avg_price * quantity) * 100) if avg_price > 0 else 0
                    
                    pos["current_price"] = current_price
                    pos["market_value"] = market_value
                    pos["unrealized_pnl"] = unrealized_pnl
                    pos["unrealized_pnl_pct"] = unrealized_pnl_pct
                    pos["updated_at"] = datetime.now().isoformat()
                    
                    total_unrealized_pnl += unrealized_pnl
            
            # 更新持仓文件
            self._save_data(self.positions_file, positions_data)
            
            # 更新投资组合
            await self._update_portfolio_pnl(total_unrealized_pnl)
            
        except Exception as e:
            logger.error(f"更新持仓市值失败: {e}")
    
    async def _update_portfolio_pnl(self, total_unrealized_pnl: float):
        """更新投资组合盈亏"""
        try:
            portfolio_data = self._load_data(self.portfolio_file)
            if not portfolio_data:
                return
            
            # 计算持仓总市值
            positions = await self.get_positions()
            total_positions_value = sum(pos.market_value for pos in positions)
            
            # 更新投资组合
            portfolio_data["positions_value"] = total_positions_value
            portfolio_data["total_value"] = portfolio_data["cash"] + total_positions_value
            portfolio_data["unrealized_pnl"] = total_unrealized_pnl
            portfolio_data["unrealized_pnl_pct"] = (
                (total_unrealized_pnl / (portfolio_data["total_value"] - total_unrealized_pnl) * 100)
                if (portfolio_data["total_value"] - total_unrealized_pnl) > 0 else 0
            )
            portfolio_data["updated_at"] = datetime.now().isoformat()
            
            self._save_data(self.portfolio_file, portfolio_data)
            
        except Exception as e:
            logger.error(f"更新投资组合盈亏失败: {e}")
    
    async def get_portfolio(self, user_id: int = 1) -> Portfolio:
        """获取投资组合"""
        try:
            portfolio_data = self._load_data(self.portfolio_file)
            if portfolio_data and portfolio_data.get("user_id") == user_id:
                # 转换为Portfolio对象
                portfolio = Portfolio(
                    user_id=portfolio_data["user_id"],
                    total_value=portfolio_data["total_value"],
                    cash=portfolio_data["cash"],
                    positions_value=portfolio_data["positions_value"],
                    unrealized_pnl=portfolio_data["unrealized_pnl"],
                    unrealized_pnl_pct=portfolio_data["unrealized_pnl_pct"],
                    daily_pnl=portfolio_data.get("daily_pnl", 0.0),
                    daily_pnl_pct=portfolio_data.get("daily_pnl_pct", 0.0),
                    created_at=datetime.fromisoformat(portfolio_data["created_at"]),
                    updated_at=datetime.fromisoformat(portfolio_data["updated_at"])
                )
                return portfolio
            else:
                raise ValueError("投资组合不存在")
        except Exception as e:
            logger.error(f"获取投资组合失败: {e}")
            raise
    
    async def get_positions(self, user_id: int = 1) -> List[Position]:
        """获取持仓信息"""
        try:
            positions_data = self._load_data(self.positions_file)
            if positions_data and "positions" in positions_data:
                positions = []
                for pos_data in positions_data["positions"]:
                    position = Position(
                        stock_code=pos_data["stock_code"],
                        stock_name=pos_data.get("stock_name", ""),
                        quantity=pos_data["quantity"],
                        avg_price=pos_data["avg_price"],
                        current_price=pos_data.get("current_price", pos_data["avg_price"]),
                        market_value=pos_data.get("market_value", pos_data["quantity"] * pos_data["avg_price"]),
                        unrealized_pnl=pos_data.get("unrealized_pnl", 0.0),
                        unrealized_pnl_pct=pos_data.get("unrealized_pnl_pct", 0.0),
                        created_at=datetime.fromisoformat(pos_data["created_at"]),
                        updated_at=datetime.fromisoformat(pos_data["updated_at"])
                    )
                    positions.append(position)
                return positions
            return []
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []
    
    async def get_orders(self, user_id: int = 1, status: Optional[str] = None) -> List[Order]:
        """获取订单列表"""
        try:
            orders_data = self._load_data(self.orders_file)
            if orders_data and "orders" in orders_data:
                orders = []
                for order_data in orders_data["orders"]:
                    if order_data.get("user_id") == user_id:
                        order = Order(
                            order_id=order_data["order_id"],
                            user_id=order_data["user_id"],
                            stock_code=order_data["stock_code"],
                            stock_name=order_data.get("stock_name", ""),
                            order_type=order_data["order_type"],
                            order_side=order_data["order_side"],
                            quantity=order_data["quantity"],
                            price=order_data.get("price"),
                            status=order_data["status"],
                            filled_price=order_data.get("filled_price"),
                            filled_quantity=order_data.get("filled_quantity", 0),
                            created_at=datetime.fromisoformat(order_data["created_at"]),
                            updated_at=datetime.fromisoformat(order_data["updated_at"]),
                            filled_at=datetime.fromisoformat(order_data["filled_at"]) if order_data.get("filled_at") else None
                        )
                        orders.append(order)
                
                if status:
                    orders = [order for order in orders if order.status == status]
                return orders
            return []
        except Exception as e:
            logger.error(f"获取订单失败: {e}")
            return []
    
    async def place_order(self, 
                         user_id: int,
                         stock_code: str,
                         order_type: str,
                         quantity: int,
                         price: Optional[float] = None,
                         order_side: str = "buy") -> Dict[str, Any]:
        """下单"""
        try:
            # 验证订单参数
            if quantity <= 0:
                return {"error": "数量必须大于0"}
            
            if order_type == "limit" and (price is None or price <= 0):
                return {"error": "限价单必须指定有效价格"}
            
            # 风险检查
            risk_check = await self._check_risk_limits(user_id, stock_code, quantity, price, order_side)
            if not risk_check["passed"]:
                return {"error": f"风险检查未通过: {risk_check['reason']}"}
            
            # 获取股票名称
            stock_name = await self._get_stock_name(stock_code)
            
            # 创建订单
            order = Order(
                order_id=f"order_{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                stock_code=stock_code,
                stock_name=stock_name,
                order_type=order_type,
                order_side=order_side,
                quantity=quantity,
                price=price,
                status="pending",
                filled_price=None,
                filled_quantity=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                filled_at=None
            )
            
            # 保存订单
            orders_data = self._load_data(self.orders_file) or {"orders": []}
            orders_data["orders"].append(asdict(order))
            self._save_data(self.orders_file, orders_data)
            
            # 如果是市价单，立即执行
            if order_type == "market":
                await self._execute_market_order(order)
            
            logger.info(f"订单创建成功: {order.order_id}")
            return {
                "message": "下单成功",
                "order_id": order.order_id,
                "status": order.status
            }
            
        except Exception as e:
            logger.error(f"下单失败: {e}")
            return {"error": f"下单失败: {e}"}
    
    async def _check_risk_limits(self, user_id: int, stock_code: str, quantity: int, 
                                price: Optional[float], order_side: str) -> Dict[str, Any]:
        """风险检查"""
        try:
            # 获取当前投资组合
            portfolio = await self.get_portfolio(user_id)
            
            # 计算订单价值
            order_value = quantity * (price or 100.0)  # 如果没有价格，假设100元
            
            # 检查单只股票最大仓位
            if order_value > portfolio.total_value * self.risk_limits["max_position_size"]:
                return {
                    "passed": False,
                    "reason": f"单只股票仓位超过限制({self.risk_limits['max_position_size']*100}%)"
                }
            
            # 检查现金是否足够（买入时）
            if order_side == "buy" and order_value > portfolio.cash:
                return {
                    "passed": False,
                    "reason": "现金不足"
                }
            
            # 检查持仓是否足够（卖出时）
            if order_side == "sell":
                positions = await self.get_positions(user_id)
                current_position = next((pos for pos in positions if pos.stock_code == stock_code), None)
                if not current_position or current_position.quantity < quantity:
                    return {
                        "passed": False,
                        "reason": "持仓不足"
                    }
            
            return {"passed": True, "reason": "通过"}
            
        except Exception as e:
            logger.error(f"风险检查失败: {e}")
            return {"passed": False, "reason": f"风险检查失败: {e}"}
    
    async def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        try:
            if jq_service:
                # 从聚宽获取股票名称
                stock_info = await jq_service.get_stock_info(stock_code)
                if stock_info:
                    return stock_info.get("name", stock_code)
            return stock_code
        except Exception as e:
            logger.error(f"获取股票名称失败: {e}")
            return stock_code
    
    async def _execute_market_order(self, order: Order):
        """执行市价单"""
        try:
            # 获取实时价格
            current_price = await self._get_current_price_for_order(order.stock_code)
            
            # 更新订单状态
            order.status = "filled"
            order.filled_price = current_price
            order.filled_quantity = order.quantity
            order.filled_at = datetime.now()
            order.updated_at = datetime.now()
            
            # 更新订单状态
            await self._update_order_status(order.order_id, "filled", current_price)
            
            # 更新持仓
            await self._update_positions(order)
            
            # 更新投资组合现金
            await self._update_portfolio_cash(order)
            
            logger.info(f"市价单执行完成: {order.order_id}, 成交价: {current_price}")
            
        except Exception as e:
            logger.error(f"执行市价单失败: {e}")
            # 标记订单为失败
            await self._update_order_status(order.order_id, "rejected")
    
    async def _get_current_price_for_order(self, stock_code: str) -> float:
        """获取订单执行的当前价格"""
        try:
            if stock_code in self.market_data_cache:
                return self.market_data_cache[stock_code].current_price
            
            # 如果缓存中没有，从聚宽获取
            if jq_service:
                price_data = await jq_service._get_current_price(stock_code)
                if price_data:
                    return price_data.get("price", 100.0)
            
            return 100.0  # 默认价格
        except Exception as e:
            logger.error(f"获取订单执行价格失败: {e}")
            return 100.0
    
    async def _update_order_status(self, order_id: str, status: str, filled_price: Optional[float] = None):
        """更新订单状态"""
        try:
            orders_data = self._load_data(self.orders_file)
            if orders_data and "orders" in orders_data:
                for order in orders_data["orders"]:
                    if order["order_id"] == order_id:
                        order["status"] = status
                        order["updated_at"] = datetime.now().isoformat()
                        if filled_price:
                            order["filled_price"] = filled_price
                            order["filled_quantity"] = order["quantity"]
                            order["filled_at"] = datetime.now().isoformat()
                        break
                self._save_data(self.orders_file, orders_data)
        except Exception as e:
            logger.error(f"更新订单状态失败: {e}")
    
    async def _update_positions(self, order: Order):
        """更新持仓"""
        try:
            positions_data = self._load_data(self.positions_file) or {"positions": []}
            positions = positions_data["positions"]
            
            # 查找是否已有该股票持仓
            existing_position = None
            for pos in positions:
                if pos["stock_code"] == order.stock_code:
                    existing_position = pos
                    break
            
            if existing_position:
                # 更新现有持仓
                if order.order_side == "buy":
                    existing_position["quantity"] += order.quantity
                    existing_position["avg_price"] = (
                        (existing_position["avg_price"] * existing_position["quantity"] + 
                         order.filled_price * order.quantity) / 
                        (existing_position["quantity"] + order.quantity)
                    )
                else:  # sell
                    existing_position["quantity"] -= order.quantity
                    if existing_position["quantity"] <= 0:
                        positions.remove(existing_position)
                
                existing_position["updated_at"] = datetime.now().isoformat()
            else:
                # 创建新持仓
                if order.order_side == "buy":
                    new_position = {
                        "stock_code": order.stock_code,
                        "stock_name": order.stock_name,
                        "quantity": order.quantity,
                        "avg_price": order.filled_price,
                        "market_value": order.quantity * order.filled_price,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    positions.append(new_position)
            
            # 更新持仓文件
            self._save_data(self.positions_file, positions_data)
            
        except Exception as e:
            logger.error(f"更新持仓失败: {e}")
    
    async def _update_portfolio_cash(self, order: Order):
        """更新投资组合现金"""
        try:
            portfolio_data = self._load_data(self.portfolio_file)
            if portfolio_data:
                order_value = order.quantity * order.filled_price
                
                if order.order_side == "buy":
                    portfolio_data["cash"] -= order_value
                else:  # sell
                    portfolio_data["cash"] += order_value
                
                portfolio_data["updated_at"] = datetime.now().isoformat()
                self._save_data(self.portfolio_file, portfolio_data)
                
        except Exception as e:
            logger.error(f"更新投资组合现金失败: {e}")
    
    async def cancel_order(self, user_id: int, order_id: str) -> Dict[str, Any]:
        """取消订单"""
        try:
            orders_data = self._load_data(self.orders_file)
            if orders_data and "orders" in orders_data:
                for order in orders_data["orders"]:
                    if order["order_id"] == order_id and order["user_id"] == user_id:
                        if order["status"] == "pending":
                            order["status"] = "cancelled"
                            order["updated_at"] = datetime.now().isoformat()
                            self._save_data(self.orders_file, orders_data)
                            return {"message": "订单取消成功"}
                        else:
                            return {"error": "只能取消待执行的订单"}
                
                return {"error": "订单不存在"}
            return {"error": "订单数据不存在"}
            
        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            return {"error": f"取消订单失败: {e}"}
    
    async def get_market_data(self, stock_code: str) -> Optional[MarketData]:
        """获取股票市场数据"""
        try:
            if stock_code in self.market_data_cache:
                return self.market_data_cache[stock_code]
            
            # 从聚宽获取实时数据
            market_data = await self._get_stock_market_data(stock_code)
            if market_data:
                self.market_data_cache[stock_code] = market_data
            
            return market_data
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return None
    
    async def get_risk_metrics(self, user_id: int = 1) -> Dict[str, Any]:
        """获取风险指标"""
        try:
            portfolio = await self.get_portfolio(user_id)
            positions = await self.get_positions(user_id)
            
            # 计算风险指标
            total_value = portfolio.total_value
            cash = portfolio.cash
            positions_value = portfolio.positions_value
            unrealized_pnl = portfolio.unrealized_pnl
            
            # 计算最大回撤（简化版）
            max_drawdown = 0.0
            if total_value > 0:
                max_drawdown = abs(unrealized_pnl) / total_value
            
            # 计算夏普比率（简化版）
            sharpe_ratio = 0.0
            if positions_value > 0 and unrealized_pnl > 0:
                sharpe_ratio = unrealized_pnl / positions_value
            
            return {
                "total_value": total_value,
                "cash_ratio": cash / total_value if total_value > 0 else 0,
                "positions_ratio": positions_value / total_value if total_value > 0 else 0,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": portfolio.unrealized_pnl_pct,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "risk_level": self._calculate_risk_level(max_drawdown, sharpe_ratio),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取风险指标失败: {e}")
            return {"error": f"获取风险指标失败: {e}"}
    
    def _calculate_risk_level(self, max_drawdown: float, sharpe_ratio: float) -> str:
        """计算风险等级"""
        if max_drawdown > 0.15 or sharpe_ratio < -0.5:
            return "高风险"
        elif max_drawdown > 0.08 or sharpe_ratio < 0:
            return "中风险"
        else:
            return "低风险"
    
    async def execute_strategy_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """执行策略信号"""
        try:
            # 解析信号
            stock_code = signal.get("stock_code")
            action = signal.get("action")  # buy, sell, hold
            quantity = signal.get("quantity", 0)
            price = signal.get("price")
            confidence = signal.get("confidence", 0.5)
            
            if not stock_code or action == "hold":
                return {"message": "无需执行操作"}
            
            # 根据置信度调整数量
            if confidence < 0.7:
                quantity = int(quantity * 0.5)  # 低置信度减半
            
            # 执行交易
            if action == "buy":
                result = await self.place_order(
                    user_id=1,
                    stock_code=stock_code,
                    order_type="market",
                    quantity=quantity,
                    order_side="buy"
                )
            elif action == "sell":
                result = await self.place_order(
                    user_id=1,
                    stock_code=stock_code,
                    order_type="market",
                    quantity=quantity,
                    order_side="sell"
                )
            else:
                return {"error": "无效的操作类型"}
            
            return {
                "message": "策略信号执行完成",
                "signal": signal,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"执行策略信号失败: {e}")
            return {"error": f"执行策略信号失败: {e}"}

# 创建全局增强交易服务实例
enhanced_trading_service = EnhancedTradingService()
