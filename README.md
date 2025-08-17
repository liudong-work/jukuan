# 量化交易系统 (Jukuan)

[![Version](https://img.shields.io/badge/version-v1.1.0-blue.svg)](https://github.com/liudong-work/jukuan/releases)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-2.0+-orange.svg)](https://dash.plotly.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

> 基于聚宽API的智能量化交易平台，提供完整的策略开发、回测分析和股票筛选功能

## 🚀 最新版本 v1.1.0

**发布日期**: 2025-08-17

### ✨ 新功能特性
- **聚宽登录管理模块化重构** - 完整的登录/退出/状态管理
- **智能界面状态管理** - 动态界面切换和状态同步
- **自选股持久化存储** - 本地配置文件和云端同步
- **高级股票筛选策略** - 多条件智能筛选

### 🔧 技术改进
- 修复重复组件ID问题
- 优化回调函数冲突处理
- 改进错误处理和日志记录
- 统一聚宽连接状态检查

### 🎨 用户体验提升
- 界面布局优化和响应式设计
- 按钮尺寸和间距调整
- 状态反馈和交互优化

---

## 📋 功能特性

- 📊 聚宽实时数据获取（A股、港股、美股、期货等）
- 🎯 多种交易策略（趋势跟踪、均值回归、机器学习等）
- 🔍 **智能策略选股**（均线交叉、KDJ+MACD、放量突破、RSI超卖等）
- 📈 完整的回测引擎
- 🛡️ 风险管理模块
- 💹 聚宽实盘交易执行
- 📊 性能分析和可视化
- 🌐 Web界面管理

## 聚宽接口优势

- 专业级金融数据（实时行情、财务数据、新闻资讯等）
- 强大的回测引擎
- 实盘交易接口
- 丰富的策略库和社区资源

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置聚宽接口

1. 注册聚宽账号：https://www.joinquant.com/
2. 获取API Token
3. 创建 `.env` 文件并配置：

```env
JQ_USERNAME=your_username
JQ_PASSWORD=your_password
JQ_TOKEN=your_token
```

## 快速开始

1. 配置环境变量
2. 运行示例策略：`python examples/jq_simple_strategy.py`
3. 运行选股示例：`python examples/stock_screening_example.py`
4. 启动Web界面：`python app.py`

## 项目结构

```
jukuan/
├── src/                    # 核心源代码
│   ├── data/              # 聚宽数据获取模块
│   ├── strategies/        # 交易策略
│   ├── backtest/          # 回测引擎
│   ├── risk/              # 风险管理
│   ├── execution/         # 聚宽交易执行
│   └── analysis/          # 性能分析
├── examples/              # 示例代码
├── tests/                 # 测试文件
├── config/                # 配置文件
├── data/                  # 数据存储
└── app.py                 # Web应用入口
```

## 使用说明

详细使用说明请参考各模块的文档和示例代码。
