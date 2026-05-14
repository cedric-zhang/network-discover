# 网络设备发现平台 · Claude Code 开发上下文

> **最后更新**: 2026-05-14 | **当前版本**: v0.9.1 | **状态**: 已发布 (仪表盘数据可视化)

---

## 🚨 环境强制声明（不遵守 = 任务作废）

> **你的运行环境是本地开发机 (Windows)，但项目只在远程服务器上！**
> **📍 唯一合法的开发目录**: `192.168.88.94:/root/network-discovery`
> **🔑 唯一合法的操作方式**: 通过 `ssh root@192.168.88.94` 执行所有命令

---

## 📊 当前状态 (v0.9.1)

### ✅ 已完成
*   **v0.9.0**: 定时扫描配置页面、Schedules CRUD API、SQLite WAL 模式、全局扫描锁。
*   **v0.9.1**: 仪表盘数据可视化增强
    - IP 状态环形图（在线/离线/未知比例）
    - 厂商/OS 分布条形图（Top 5）
    - Chart.js CDN 引入，深色主题适配
    - CDN 容错降级提示

### ⏭️ 下一步计划
*   **v0.10.0 候选**: CSV 导出、资产趋势图表、OS 检测增强。

---

## 📁 项目结构
```
/root/network-discovery/
├── app/
│   ├── main.py          # FastAPI 入口 (version: 0.9.1)
│   ├── models.py        # SQLAlchemy 模型
│   ├── routers/
│   │   ├── schedules.py # 计划任务 API
│   │   └── ...
├── static/
│   ├── css/style.css    # 全局样式 (含图表样式)
│   └ js/app.js          # 前端逻辑 (含 Chart.js 渲染)
├── index.html           # 仪表盘 (含图表 canvas)
└── schedules.html       # 计划任务页面
```

---

## 🛠️ 开发规范

1. **Git 连续性**: 每次 Commit 前必须更新 CLAUDE.md。
2. **版本动态化**: 前端通过 /health 动态加载版本号。
