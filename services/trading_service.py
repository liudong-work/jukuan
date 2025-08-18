"""
交易服务模块
提供投资组合管理、持仓管理、订单管理等功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import json
import os

logger = logging.getLogger(__name__)

class TradingService:
    """交易服务类"""
    
    def __init__(self):
        self.portfolio_file = "data/portfolio.json"
        self.orders_file = "data/orders.json"
        self.positions_file = "data/positions.json"
        self._ensure_data_dir()
    
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
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据失败 {file_path}: {e}")
    
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
    
    async def get_portfolio(self, user_id: int = 1) -> Dict[str, Any]:
        """获取投资组合"""
        try:
            portfolio = self._load_data(self.portfolio_file)
            if portfolio and portfolio.get("user_id") == user_id:
                # 计算实时持仓价值
                positions = await self.get_positions(user_id)
                total_positions_value = sum(pos.get("market_value", 0) for pos in positions)
                
                portfolio["positions_value"] = total_positions_value
                portfolio["total_value"] = portfolio["cash"] + total_positions_value
                portfolio["updated_at"] = datetime.now().isoformat()
                
                # 更新投资组合
                self._save_data(self.portfolio_file, portfolio)
                
                return portfolio
            else:
                return {"error": "投资组合不存在"}
        except Exception as e:
            logger.error(f"获取投资组合失败: {e}")
            return {"error": f"获取投资组合失败: {e}"}
    
    async def get_positions(self, user_id: int = 1) -> List[Dict[str, Any]]:
        """获取持仓信息"""
        try:
            positions_data = self._load_data(self.positions_file)
            if positions_data and "positions" in positions_data:
                return positions_data["positions"]
            return []
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []
    
    async def get_orders(self, user_id: int = 1, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取订单列表"""
        try:
            orders_data = self._load_data(self.orders_file)
            if orders_data and "orders" in orders_data:
                orders = orders_data["orders"]
                if status:
                    orders = [order for order in orders if order.get("status") == status]
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
            
            # 创建订单
            order = {
                "order_id": f"order_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "stock_code": stock_code,
                "order_type": order_type,
                "order_side": order_side,
                "quantity": quantity,
                "price": price,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # 保存订单
            orders_data = self._load_data(self.orders_file) or {"orders": []}
            orders_data["orders"].append(order)
            self._save_data(self.orders_file, orders_data)
            
            # 如果是市价单，立即执行
            if order_type == "market":
                await self._execute_market_order(order)
            
            logger.info(f"订单创建成功: {order['order_id']}")
            return {
                "message": "下单成功",
                "order_id": order["order_id"],
                "status": order["status"]
            }
            
        except Exception as e:
            logger.error(f"下单失败: {e}")
            return {"error": f"下单失败: {e}"}
    
    async def _execute_market_order(self, order: Dict[str, Any]):
        """执行市价单"""
        try:
            # 模拟市价单执行
            order["status"] = "filled"
            order["filled_price"] = order.get("price", 100.0)  # 模拟成交价格
            order["filled_at"] = datetime.now().isoformat()
            order["updated_at"] = datetime.now().isoformat()
            
            # 更新订单状态
            await self._update_order_status(order["order_id"], "filled")
            
            # 更新持仓
            await self._update_positions(order)
            
            logger.info(f"市价单执行完成: {order['order_id']}")
            
        except Exception as e:
            logger.error(f"执行市价单失败: {e}")
    
    async def _update_order_status(self, order_id: str, status: str):
        """更新订单状态"""
        try:
            orders_data = self._load_data(self.orders_file)
            if orders_data and "orders" in orders_data:
                for order in orders_data["orders"]:
                    if order["order_id"] == order_id:
                        order["status"] = status
                        order["updated_at"] = datetime.now().isoformat()
                        break
                self._save_data(self.orders_file, orders_data)
        except Exception as e:
            logger.error(f"更新订单状态失败: {e}")
    
    async def _update_positions(self, order: Dict[str, Any]):
        """更新持仓"""
        try:
            positions_data = self._load_data(self.positions_file) or {"positions": []}
            positions = positions_data["positions"]
            
            # 查找是否已有该股票持仓
            existing_position = None
            for pos in positions:
                if pos["stock_code"] == order["stock_code"]:
                    existing_position = pos
                    break
            
            if existing_position:
                # 更新现有持仓
                if order["order_side"] == "buy":
                    existing_position["quantity"] += order["quantity"]
                    existing_position["avg_price"] = (
                        (existing_position["avg_price"] * existing_position["quantity"] + 
                         order["filled_price"] * order["quantity"]) / 
                        (existing_position["quantity"] + order["quantity"])
                    )
                else:  # sell
                    existing_position["quantity"] -= order["quantity"]
                    if existing_position["quantity"] <= 0:
                        positions.remove(existing_position)
            else:
                # 创建新持仓
                if order["order_side"] == "buy":
                    new_position = {
                        "stock_code": order["stock_code"],
                        "quantity": order["quantity"],
                        "avg_price": order["filled_price"],
                        "market_value": order["quantity"] * order["filled_price"],
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    positions.append(new_position)
            
            # 更新持仓文件
            self._save_data(self.positions_file, positions_data)
            
        except Exception as e:
            logger.error(f"更新持仓失败: {e}")
    
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

# 创建全局交易服务实例
trading_service = TradingService()
