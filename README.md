# 量化交易系统 (Jukuan) v2.0.0

[![Version](https://img.shields.io/badge/version-v2.0.0-blue.svg)](https://github.com/liudong-work/jukuan/releases)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-orange.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

> 🚀 **全新2.0版本** - 基于FastAPI的现代化量化交易平台，提供完整的策略开发、回测分析、自动交易和风险管理功能

## 🌟 2.0版本重大升级

### ✨ 全新架构特性
- **🏗️ 微服务架构** - 模块化设计，易于扩展和维护
- **🚀 异步处理** - 基于FastAPI的高性能异步框架
- **💾 数据持久化** - PostgreSQL + Redis 双数据库架构
- **🔐 安全增强** - JWT认证 + RBAC权限控制
- **📊 实时监控** - Prometheus + Grafana 监控体系

### 🎯 核心功能升级
- **📈 实时行情** - WebSocket实时数据推送
- **🤖 智能交易** - 完整的自动交易执行系统
- **🛡️ 风险控制** - 多层次风险管理框架
- **📱 移动端** - 响应式设计，支持多设备访问
- **🌐 国际化** - 多语言支持

---

## 📋 功能特性

### 📊 数据管理
- 聚宽实时数据获取（A股、港股、美股、期货等）
- WebSocket实时行情推送
- 历史数据管理和缓存
- 财务数据和基本面分析

### 🎯 策略系统
- 多种交易策略（趋势跟踪、均值回归、机器学习等）
- 智能策略选股（均线交叉、KDJ+MACD、放量突破、RSI超卖等）
- 策略回测和优化
- 策略组合管理

### 🤖 自动交易
- 完整的自动交易执行系统
- 实时信号生成和处理
- 智能订单路由和执行
- 持仓和资金管理

### 🛡️ 风险管理
- 多层次风险控制框架
- 实时风险监控和预警
- 动态风险调整
- 合规性检查

### 📈 分析工具
- 完整的回测引擎
- 性能分析和可视化
- 实时监控仪表板
- 报告生成系统

## 🏗️ 技术架构

### 后端架构
```
jukuan/
├── api/                    # FastAPI接口层
│   ├── v1/               # API版本1
│   ├── v2/               # API版本2
│   └── middleware/       # 中间件
├── core/                  # 核心模块
│   ├── config/           # 配置管理
│   ├── security/         # 安全认证
│   └── database/         # 数据库管理
├── services/              # 业务服务层
│   ├── trading/          # 交易服务
│   ├── strategy/         # 策略服务
│   ├── risk/             # 风险管理
│   └── analysis/         # 分析服务
├── models/                # 数据模型
├── utils/                 # 工具函数
└── tests/                 # 测试文件
```

### 前端架构
```
frontend/
├── components/            # 可复用组件
├── pages/                 # 页面组件
├── hooks/                 # 自定义Hooks
├── services/              # API服务
├── store/                 # 状态管理
└── utils/                 # 工具函数
```

## 🚀 快速开始

### 环境要求
- Python 3.9+
- PostgreSQL 13+
- Redis 6+

### 安装依赖

#### 后端依赖
```bash
pip install -r requirements.txt
```

#### 前端依赖
```bash
cd frontend
npm install
```

### 配置环境

1. 复制环境配置文件：
```bash
cp .env.example .env
```

2. 配置数据库连接：
```env
DATABASE_URL=postgresql://user:password@localhost/jukuan
REDIS_URL=redis://localhost:6379
```

3. 配置聚宽接口：
```env
JQ_USERNAME=your_username
JQ_PASSWORD=your_password
JQ_TOKEN=your_token
```

### 启动服务

#### 启动后端
```bash
# 开发模式
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

#### 启动前端
```bash
cd frontend
npm run dev
```

#### 启动数据库
```bash
# PostgreSQL
docker run -d --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:13

# Redis
docker run -d --name redis -p 6379:6379 redis:6
```

## 📚 使用说明

### API文档
启动服务后访问：`http://localhost:8000/docs`

### 示例代码
查看 `examples/` 目录下的示例代码

### 策略开发
参考 `docs/strategy_development.md` 进行策略开发

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_trading.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 📦 部署

### Docker部署
```bash
docker-compose up -d
```

### 生产环境部署
参考 `docs/deployment.md`

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系我们

- 项目主页：https://github.com/liudong-work/jukuan
- 问题反馈：https://github.com/liudong-work/jukuan/issues
- 邮箱：liudong.work@example.com

---

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**
