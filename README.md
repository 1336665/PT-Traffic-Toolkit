<div align="center">

# PT Traffic Toolkit

### 智能 PT 流量管理工具

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)](https://vuejs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

**一站式 PT 下载管理平台，让你的 PT 生活更加智能高效**

[功能特点](#-功能特点) · [快速开始](#-快速开始) · [使用指南](#-使用指南) · [技术架构](#-技术架构)

</div>

---

## 🎯 功能特点

<table>
<tr>
<td width="50%">

### 📊 实时仪表盘
- 实时速度监控与图表展示
- 存储空间统计与预警
- 活动时间线追踪
- 多下载器状态汇总

</td>
<td width="50%">

### 🔗 多下载器支持
- qBittorrent 完整支持
- Transmission 完整支持
- Deluge 完整支持
- 自动负载均衡与故障转移

</td>
</tr>
<tr>
<td width="50%">

### 📡 RSS 智能订阅
- 多 RSS 源管理
- Free 种自动识别
- HR 种智能排除
- 体积/做种数过滤
- 关键词包含/排除规则

</td>
<td width="50%">

### 🗑️ 智能删种规则
- 可视化规则编辑器
- 多条件组合逻辑
- 条件持续时间检测
- 删种前强制汇报
- 支持保留或删除文件

</td>
</tr>
<tr>
<td width="50%">

### ⚡ 动态限速系统
- PID 控制器精准限速
- 卡尔曼滤波速度预测
- 多窗口速度追踪
- 站点级独立规则
- 阶段划分：预热→追赶→稳定→完成

</td>
<td width="50%">

### ✨ U2 魔法抓取
- 自动识别 Free 种子
- 做种人数限制
- 体积范围过滤
- 新旧种优先级控制
- 分类过滤与备份支持

</td>
</tr>
</table>

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/yourusername/PT-Traffic-Toolkit.git
cd PT-Traffic-Toolkit

# 运行安装脚本
chmod +x install.sh
./install.sh
```

安装完成后访问 `http://localhost:8080` 即可使用。

### 方式二：交互式管理脚本

```bash
chmod +x pt-manager.sh
./pt-manager.sh
```

脚本提供以下功能：
- 🔧 安装 / 启动 / 停止 / 重启
- 📦 更新到最新版本
- 📊 查看运行状态
- 📝 查看实时日志

### 方式三：手动安装

<details>
<summary>展开查看手动安装步骤</summary>

#### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

</details>

---

## ⚙️ 配置说明

### 环境变量

复制 `.env.example` 为 `.env` 并修改配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | JWT 密钥（生产环境必须修改） | `change-this-in-production` |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite+aiosqlite:///./data/pt_manager.db` |
| `DEBUG` | 调试模式 | `false` |
| `TELEGRAM_BOT_TOKEN` | Telegram 通知机器人 Token | - |
| `TELEGRAM_CHAT_ID` | Telegram 通知 Chat ID | - |

### 首次使用

1. 访问 `http://localhost:8080`
2. 创建管理员账号
3. 添加下载器（支持 qBittorrent / Transmission / Deluge）
4. 根据需要配置 RSS、删种规则等功能

---

## 📖 使用指南

### 下载器管理

- 支持同时管理多个下载器
- 5 分钟自动汇报 Tracker
- 首尾块优先下载
- 实时磁盘空间监控
- 连接数智能限制

### RSS 选种策略

| 功能 | 说明 |
|------|------|
| Free 种识别 | 支持配置站点 Cookie 自动识别 |
| HR 排除 | 自动跳过 HR 种子 |
| 体积过滤 | 设置最小/最大体积限制 |
| 做种数过滤 | 根据做种人数筛选 |
| 关键词规则 | 支持包含/排除关键词 |
| 智能选择 | 自动选择空闲空间最多的下载器 |

### 删种规则条件

支持以下条件组合：
- 📈 进度、做种时间、分享率
- 📊 上传/下载量与速度
- 💾 体积、做种数、吸血数
- 🏷️ Tracker、标签、状态
- ⏱️ 条件持续时间（需满足 X 秒）

### 动态限速原理

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   预热阶段   │ →  │   追赶阶段   │ →  │   稳定阶段   │
│  Warm Up    │    │   Catch Up  │    │   Stable    │
└─────────────┘    └─────────────┘    └─────────────┘
      ↓                   ↓                   ↓
   渐进提速           快速逼近           精准维持
```

- **PID 控制器**：根据误差动态调整限速值
- **卡尔曼滤波**：预测速度变化趋势，减少波动
- **多窗口追踪**：短期/中期/长期速度分别监控

---

## 🛠️ 技术架构

### 后端技术栈

| 技术 | 用途 |
|------|------|
| FastAPI | 高性能异步 Web 框架 |
| SQLAlchemy 2.0 | ORM 数据库操作 |
| SQLite | 轻量级数据存储 |
| APScheduler | 定时任务调度 |
| httpx | 异步 HTTP 客户端 |
| qbittorrent-api | qBittorrent 客户端 |
| transmission-rpc | Transmission 客户端 |
| deluge-client | Deluge 客户端 |

### 前端技术栈

| 技术 | 用途 |
|------|------|
| Vue 3 | 渐进式前端框架 |
| Vite | 下一代构建工具 |
| Tailwind CSS | 原子化 CSS 框架 |
| Headless UI | 无样式组件库 |
| ECharts | 数据可视化图表 |
| Pinia | 状态管理 |
| Vue Router | 路由管理 |

---

## 📡 API 文档

后端运行时访问以下地址查看交互式 API 文档：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

<div align="center">

**如果这个项目对你有帮助，欢迎 Star ⭐**

Made with ❤️ for PT Community

</div>
