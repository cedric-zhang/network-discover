# 网络设备发现平台 — Claude Code 开发上下文

> 最近更新: 2026-05-20 | 当前版本: **v0.10.2** | 状态: ✅ v0.10.2 已验收通过

## 🚨 开发铁律（每次启动必读）

1. **SSH 强制**：必须在 `192.168.88.94` 的 `/root/network-discovery` 下操作，**禁止本地开发**
   - 每次操作前先确认: `ssh root@192.168.88.94 "hostname"` 输出不是 Windows 路径
   - **所有命令必须带 SSH 前缀**: `ssh root@192.168.88.94 "cd /root/network-discovery && ..."`
   - 在本地 `C:\Users\ai` 创建/修改任何项目文件 = 违规
2. **禁止 `git init`**：仓库已存在，只能 `git add/commit/push`
3. **版本号规则**：功能迭代 `+0.1.0`，Bug 修复 `+0.0.1`。版本号变更权归军师，严禁自行修改
4. **每次 commit**：提交信息格式 `[类型] 具体做了什么`

## 🚨 Bug 修复强制流程（每个 Bug 独立执行，不得跳过）

### Step 0：诊断（不改代码，先理解现状）
```bash
# 1. 找到相关代码
grep -n '函数名/元素ID/CSS类' 文件路径
# 2. 确认 API 是否正常（排除后端问题）
curl -s -H "Host: network-discover.irigud.com" http://192.168.88.94:800/api/xxx
# 3. 写 1-2 句话根因分析
```

### Step 1：修复
- 只改相关文件，不碰无关代码
- 前端必须同时检查：**HTML 结构 + CSS 样式 + JS 逻辑 + 事件绑定**
- 常见坑：
  - `getElementById("x")` 与 HTML 中 `id="y"` 不匹配
  - CSS `!important` 覆盖新样式
  - `addEventListener` 重复绑定未移除旧的
  - 全局变量被 filter/覆盖后污染后续逻辑

### Step 2：自测（交付前必须执行，贴结果）
```bash
# 1. grep 确认修改已写入
grep -n '关键代码片段' 文件路径
# 2. curl 测试 API（如涉及后端）
curl -s -H "Host: network-discover.irigud.com" http://192.168.88.94:800/api/xxx
# 3. 检查三个页面 console 无报错
```

### Step 3：交付（禁止只说"已修复"）
必须按以下格式回复：
```
| Bug | 根因 | 修改文件 | grep 验证结果 | curl/API 验证结果 |
```
军师复测前，自测结果必须全部通过。

## 📋 版本历史

| 版本 | 内容 | 状态 |
|------|------|------|
| v0.1.0 | UI 骨架 — 深色 Bento Grid + CSS 变量 + 3 页面 | ✅ |
| v0.2.0 | FastAPI + Pydantic + 4 REST API | ✅ |
| v0.3.0 | nmap CLI 封装 + 异步扫描 + XML 解析 | ✅ |
| v0.4.0 | SQLite + SQLAlchemy + IP Upsert 持久化 | ✅ |
| v0.5.0 | APScheduler 定时扫描集成 | ✅ |
| v0.6.0 | Vanilla JS 真实数据绑定 + Nginx/Systemd 部署 | ✅ |
| v0.9.9-fix1~12 | 分页/批量删除/弹窗修复/QA体系/周期编辑等 | ✅ |
| v0.10.0 | fix 系列闭环里程碑 | ✅ |
| v0.10.1 | systemd 服务 + Nginx 域名路由 + README 双语 + GitHub 推送 | ✅ |
| v0.10.2 | 扫描异步化 + 进度轮询 + 预估时间 + 状态筛选修复 | ✅ |

### 历史教训（重要，避免重蹈覆辙）

- **前端 Bug 不能只看症状**：必须 grep 找根因（如 renderTasks 没调用 getFilteredTasks）
- **局部修复会引入新 Bug**：修 A 后必须回归测 B、C
- **ID 匹配是最常见的坑**：JS 里的 getElementById 必须与 HTML 中的 id 完全一致
- **CSS !important 是毒药**：尽量不用，用了会导致后续样式不生效
- **任务卡描述必须精确**：写函数名/行号/HTML 结构，不要写"修复 XX"

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
├── frontend/
│   ├── scan.html         # 扫描页
│   ├── tasks.html        # 扫描任务页
│   ├── assets.html       # 资产清单
│   └── index.html        # 仪表盘
├── tests/
│   ├── test_api.py
│   ├── test_scanner.py
│   ├── test_scheduler.py
│   └── ui-validate.sh
├── deploy.sh
└── requirements.txt
```

## 🔧 当前环境

- **服务器**: `192.168.88.94` (RockyLinux 9.7)
- **项目路径**: `/root/network-discovery`
- **服务运行**: Systemd (`network-discovery.service`) → Uvicorn `127.0.0.1:8000`
- **Nginx**: 监听 800 端口，基于域名路由，需带 `Host: network-discover.irigud.com`
- **数据库**: SQLite (`/root/network-discovery/app/network_discovery.db`)
- **验收通道**: `curl -H "Host: network-discover.irigud.com" http://192.168.88.94:800/...`

## 🎨 UI 设计规范

- 深色主题: 背景 `#0f1923`，卡片 `#1e2d3d`
- 无实线边框，用柔和弥散阴影 + 大圆角 12px
- Bento Grid 布局，响应式
- 功能色：绿在线/红离线/蓝交互
- 禁止原生 `confirm/alert/prompt`，强制自定义弹窗

## ⏭️ 下一步方向（待确认）

v0.10.2 已闭环。后续候选方向：
1. 资产详情页（单 IP 端口/服务/OS 详情）
2. CSV/Excel 导出
3. 扫描任务调度编辑器优化

**等待军师生成下一版本任务卡后再开始开发。**
