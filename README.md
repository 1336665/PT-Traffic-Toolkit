<div align="center">

<img src="https://img.shields.io/badge/PT%20Manager-Pro-6366f1?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyek0xMCAzLjVjLjgzIDAgMS41LjY3IDEuNSAxLjVzLS42NyAxLjUtMS41IDEuNS0xLjUtLjY3LTEuNS0xLjUuNjctMS41IDEuNS0xLjV6bTAgMTRjLTIuNjEgMC00LjczLTIuMTItNC43My00LjczczIuMTItNC43MyA0LjczLTQuNzMgNC43MyAyLjEyIDQuNzMgNC43My0yLjEyIDQuNzMtNC43MyA0LjczeiIvPjwvc3ZnPg==" alt="PT Manager Pro">

# PT Manager Pro

### 🚀 智能 PT 流量管理平台

[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.4-4FC08D?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)

**一站式 Private Tracker 下载管理解决方案**

[✨ 功能特点](#-功能特点) · [🚀 快速开始](#-快速开始) · [📖 使用指南](#-使用指南) · [🛠️ 技术架构](#️-技术架构)

---

<img src="https://img.shields.io/badge/状态-活跃开发中-success?style=for-the-badge" alt="Status">

</div>

## ✨ 功能特点

<table>
<tr>
<td width="50%" valign="top">

### 📊 实时仪表盘
- 🔄 实时上传/下载速度监控
- 📈 可视化速度历史图表（1h/6h/24h）
- 💾 今日流量统计与分享率计算
- 🖥️ 多下载器状态聚合展示
- 📋 活动时间线实时追踪

</td>
<td width="50%" valign="top">

### 🔗 多下载器支持
- ✅ **qBittorrent** - 完整 WebUI API 支持
- ✅ **Transmission** - RPC 协议支持
- ✅ **Deluge** - JSON-RPC 支持
- 🔀 智能负载均衡与故障转移
- 📡 自动 Tracker 汇报

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📡 RSS 智能订阅
- 🆓 Free/2xFree 种子自动识别
- ⚠️ HR (Hit & Run) 种子排除
- 📏 体积范围过滤 (Min/Max)
- 👥 做种人数智能筛选
- 🔤 关键词包含/排除规则
- 🍪 Cookie 支持私有站点

</td>
<td width="50%" valign="top">

### 🗑️ 智能删种规则
- 🎨 可视化规则编辑器
- 🔗 多条件 AND/OR 组合
- ⏱️ 条件持续时间检测
- 📢 删种前强制 Tracker 汇报
- 📁 可选保留/删除文件
- 📱 Telegram 删种通知

</td>
</tr>
<tr>
<td width="50%" valign="top">

### ⚡ 动态限速系统
- 🎛️ PID 控制器精准调速
- 📊 卡尔曼滤波速度预测
- 📈 多时间窗口速度追踪
- 🏷️ 站点级独立限速规则
- 🔄 四阶段控制：预热 → 追赶 → 稳定 → 完成

</td>
<td width="50%" valign="top">

### ✨ U2 魔法抓取
- 🎁 自动识别 Free/2xFree 种子
- 👥 做种人数限制过滤
- 📏 体积范围智能筛选
- 🆕 新旧种优先级控制
- 📂 分类过滤与备份支持

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🌐 Netcup 流量监控
- 📊 VPS 流量使用监控
- ⚠️ 限速状态自动检测
- 🔔 限速预警通知
- 📈 流量趋势分析

</td>
<td width="50%" valign="top">

### 🔔 通知系统
- 📱 Telegram Bot 推送
- 📋 RSS 下载通知
- 🗑️ 删种操作通知
- ⚠️ 系统异常告警

</td>
</tr>
</table>

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/1336665/PT-Traffic-Toolkit.git
cd PT-Traffic-Toolkit

# 复制环境配置
cp .env.example .env

# 启动服务
docker-compose up -d
```

🎉 访问 `http://localhost:8080` 开始使用！

### 方式二：管理脚本

```bash
chmod +x pt-manager.sh
./pt-manager.sh
```

脚本功能：
| 选项 | 功能 |
|------|------|
| 🔧 Install | 安装并启动服务 |
| ▶️ Start | 启动服务 |
| ⏹️ Stop | 停止服务 |
| 🔄 Restart | 重启服务 |
| 📊 Status | 查看运行状态 |
| 📝 Logs | 查看实时日志 |
| 📦 Update | 更新到最新版本 |

### 方式三：手动部署

<details>
<summary>📦 展开查看手动部署步骤</summary>

#### 后端服务

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 前端服务

```bash
cd frontend
npm install
npm run build
# 使用 nginx 或其他静态服务器托管 dist 目录
```

</details>

---

## ⚙️ 配置说明

### 环境变量

复制 `.env.example` 为 `.env` 并修改：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | JWT 密钥 ⚠️ **生产环境必须修改** | `change-this-in-production` |
| `DATABASE_URL` | 数据库连接 | `sqlite+aiosqlite:///./data/pt_manager.db` |
| `DEBUG` | 调试模式 | `false` |
| `TIMEZONE` | 时区设置 | `Asia/Shanghai` |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | - |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | - |

### 首次使用

1. 🌐 访问 `http://localhost:8080`
2. 👤 创建管理员账号
3. ➕ 添加下载器 (qBittorrent / Transmission / Deluge)
4. ⚙️ 配置 RSS 订阅、删种规则等功能

---

## 📖 使用指南

### 下载器管理

| 功能 | 说明 |
|------|------|
| 🔌 多客户端 | 同时管理多个下载器实例 |
| 📡 自动汇报 | 新种子 5 分钟后自动汇报 Tracker |
| 💾 空间监控 | 实时磁盘空间预警 |
| 🔄 故障转移 | 自动切换到健康下载器 |

### RSS 选种策略

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  获取 RSS   │ ──▶ │  条件过滤   │ ──▶ │  下载种子   │
│   Feed      │     │  Filter     │     │  Download   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Free检测      体积过滤     关键词匹配
```

### 删种规则条件

支持以下条件的任意组合：

| 类别 | 条件 |
|------|------|
| 📈 进度相关 | 完成进度、做种时间、分享率 |
| 📊 流量相关 | 上传量、下载量、上传速度、下载速度 |
| 💾 存储相关 | 种子体积、总大小 |
| 👥 连接相关 | 做种数、吸血数、连接数 |
| 🏷️ 标签相关 | Tracker、标签、分类、状态 |
| ⏱️ 时间相关 | 添加时间、完成时间、持续时间 |

### 动态限速原理

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  🔥 预热    │ ─▶ │  🏃 追赶    │ ─▶ │  ⚖️ 稳定    │ ─▶ │  ✅ 完成    │
│  Warm Up   │    │  Catch Up  │    │   Stable   │    │  Complete  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                  │                  │                  │
   渐进提速          快速逼近          精准维持          目标达成
```

- **PID 控制器**：根据速度误差动态调整限速值
- **卡尔曼滤波**：预测速度趋势，平滑波动
- **多窗口追踪**：短期 (30s) / 中期 (2min) / 长期 (5min) 分别监控

---

## 🛠️ 技术架构

### 后端 (Python)

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.109+ | 高性能异步 Web 框架 |
| SQLAlchemy | 2.0+ | 异步 ORM 数据库操作 |
| SQLite | 3.x | 轻量级嵌入式数据库 |
| APScheduler | 3.x | 定时任务调度器 |
| httpx | 0.26+ | 异步 HTTP 客户端 |
| Pydantic | 2.x | 数据验证与序列化 |

### 前端 (Vue.js)

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.4+ | 渐进式前端框架 |
| Vite | 5.x | 下一代构建工具 |
| Tailwind CSS | 3.4+ | 原子化 CSS 框架 |
| Headless UI | 1.7+ | 无样式组件库 |
| ECharts | 5.4+ | 数据可视化图表 |
| Pinia | 2.x | 状态管理 |
| Vue Router | 4.x | 路由管理 |
| Axios | 1.6+ | HTTP 客户端 |
| Day.js | 1.11+ | 日期时间处理 |

### 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                      Docker Compose                      │
├─────────────────────────┬───────────────────────────────┤
│      Frontend           │          Backend              │
│   ┌─────────────────┐   │   ┌───────────────────────┐   │
│   │  Nginx (Alpine) │   │   │   Python 3.11-slim    │   │
│   │   Static Files  │◀──┼───│   FastAPI + Uvicorn   │   │
│   └─────────────────┘   │   └───────────┬───────────┘   │
│          :8080          │               │  :8000        │
└─────────────────────────┴───────────────┼───────────────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │   SQLite     │
                                   │   Database   │
                                   └──────────────┘
```

---

## 📡 API 文档

后端运行时访问交互式 API 文档：

| 文档 | 地址 |
|------|------|
| 📘 Swagger UI | `http://localhost:8000/docs` |
| 📗 ReDoc | `http://localhost:8000/redoc` |

---

## 🔧 常见问题

<details>
<summary><b>Q: 如何重置管理员密码？</b></summary>

删除 `data/pt_manager.db` 数据库文件后重启服务，将引导您重新创建管理员账号。

</details>

<details>
<summary><b>Q: 如何备份数据？</b></summary>

备份 `data/` 目录下的所有文件即可，包含数据库和配置。

</details>

<details>
<summary><b>Q: 支持 HTTPS 吗？</b></summary>

建议使用反向代理（如 Nginx、Caddy）配置 SSL 证书。

</details>

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. 🍴 Fork 本仓库
2. 🌿 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 💾 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 📤 推送分支 (`git push origin feature/AmazingFeature`)
5. 🔀 提交 Pull Request

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

<div align="center">

**如果这个项目对你有帮助，欢迎 Star ⭐**

<br>

[![Star History Chart](https://img.shields.io/badge/⭐-Star%20This%20Repo-yellow?style=for-the-badge)](https://github.com/yourusername/PT-Manager-Pro)

<br>

Made with ❤️ for PT Community

<sub>Copyright © 2024 PT Manager Pro. All rights reserved.</sub>

</div>
