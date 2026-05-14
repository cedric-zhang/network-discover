# 网络设备发现平台 — Claude Code 开发上下文

> 生成时间: 2026-05-13 | 当前版本: **v0.8.1** | 状态: ✅ 端口详情补全与版本治理完成

## 🚨 开发铁律（每次启动必读）

1. **SSH 强制**：必须在 `192.168.88.94` 的 `/root/network-discovery` 下操作，**禁止本地开发**
2. **禁止 `git init`**：仓库已存在，只能 `git add/commit/push`
3. **测试门禁 (Step 0)**：开发前先跑 `cd /root/network-discovery && pytest tests/ -v`，失败先修
4. **版本号规则**：功能迭代 `+0.1.0`，Bug 修复 `+0.0.1`
5. **每次 commit**：提交信息格式 `[类型] 具体做了什么`

## 📋 v0.1.0 ~ v0.8.1 开发历程

| 版本 | 内容 | 状态 |
|------|------|------|
| v0.1.0 | UI 骨架 — 深色 Bento Grid + CSS 变量 + 3 页面 | ✅ |
| v0.2.0 | FastAPI + Pydantic + 4 REST API | ✅ |
| v0.3.0 | nmap CLI 封装 + 异步扫描 + XML 解析 | ✅ |
| v0.4.0 | SQLite + SQLAlchemy + IP Upsert 持久化 | ✅ |
| v0.5.0 | APScheduler 定时扫描集成 | ✅ |
| v0.8.1 | Vanilla JS 真实数据绑定 + Nginx/Systemd 部署 | ✅ |

### v0.8.1 修复记录（重要，避免重蹈覆辙）

- **Bug 1**：前端 API 路径 `/api/scans/` 应为 `/api/scan/submit` → 已修复
- **Bug 2**：Nginx 默认 server 块冲突 → 已注释掉 `/etc/nginx/nginx.conf` 默认 server
- **Bug 3**：`/root/network-discovery` 权限 403 → 已 `chmod 755 /root` + `chmod -R 755 /root/network-discovery`
- **Bug 4**：`scan.html` `<form>` 缺 `class="scan-form"` → 已添加
- **Bug 5**：`index.html` 硬编码假数据 → 已移除，JS 动态填充空状态

## 🏗️ 项目结构

```
/root/network-discovery/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 入口
│   ├── models.py         # SQLAlchemy 模型 (IPAsset, ScanTask, Schedule)
│   ├── schemas.py        # Pydantic schemas
│   ├── scanner.py        # nmap 封装
│   └── scheduler.py      # APScheduler
├── static/
│   ├── css/style.css     # 全局样式 + CSS 变量
│   └── js/app.js         # 前端逻辑 (Fetch API)
├── templates/
│   ├── index.html        # 仪表盘
│   ├── scan.html         # 扫描页
│   └── assets.html       # 资产清单
├── tests/
│   ├── test_api.py       # API 测试
│   ├── test_scanner.py   # nmap 测试
│   ├── test_scheduler.py # 调度测试
│   └── ui-validate.sh    # UI 结构验证
├── deploy.sh             # 部署脚本 (Systemd + Nginx)
└── requirements.txt
```

## 🔧 当前环境

- **服务器**: `192.168.88.94` (RockyLinux 9.7)
- **项目路径**: `/root/network-discovery`
- **服务运行**: Systemd (`network-discovery.service`) → Uvicorn :8000
- **Nginx**: 监听 80 → 反向代理到 `127.0.0.1:8000`
- **数据库**: SQLite (`/root/network-discovery/app/network_discovery.db`)
- **测试基线**: 50+ pytest 用例应全部 PASS

## 🎨 UI 设计规范

- 深色主题: 背景 `#0f1923`，卡片 `#222d3d`
- 无实线边框，用柔和阴影 + 大圆角
- CSS 变量集中在 `style.css` 顶部
- Bento Grid 布局，响应式

## ⏭️ 下一步方向（待确认）

v0.8.1 已闭环。后续候选方向：
1. 端到端扫描验证（跑一次真实扫描，确认数据流转）
2. 扫描进度实时反馈
3. 资产详情页（单 IP 端口/服务/OS 详情）
4. CSV/Excel 导出

**等待军师生成 v0.7.0 任务卡后再开始开发。**
