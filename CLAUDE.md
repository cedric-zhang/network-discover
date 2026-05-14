# 网络设备发现平台 — Claude Code 开发上下文

> **最后更新**: 2026-05-14 | **当前版本**: v0.8.1 | **状态**: ✅ 端口详情补全 + 12个Hotfix已完成

---

## 🚨 环境强制声明（不遵守 = 任务作废）

> **你的运行环境是本地开发机 (Windows)，但项目只在远程服务器上！**
> **唯一合法的开发目录**: 192.168.88.94:/root/network-discovery
> **唯一合法的操作方式**: 通过 ssh root@192.168.88.94 执行所有命令
> **绝对禁止**: 在本地 C:\Users\ai 创建/修改任何项目文件

**验证方法**：
ssh root@192.168.88.94 "hostname && pwd"
# 输出: ai-team /root/network-discovery

**铁律**：
1. 所有 Bash 命令必须写成 ssh root@192.168.88.94 "cd /root/network-discovery && ..." 格式
2. 绝对禁止给裸命令
3. 提交前验证语法：python3 -m py_compile *.py + node --check *.js

---

## 📊 v0.8.1 完成内容

### ✅ 功能增强
- 端口详情提取：从 nmap XML 提取 service/product/version
- 数据存储格式升级："22/tcp" → {port:22, service:ssh, product:OpenSSH, version:8.7}
- 动态版本号：从 /health API 加载，告别硬编码
- 资产详情页：完整展示端口服务信息

### 🔧 Hotfix 修复 (共12次)
| 问题类型 | 次数 | 教训 |
|---------|------|------|
| JS 语法错误 | 4 | 提交前必须 node --check |
| 元素ID不匹配 | 3 | 写 JS 前先 grep 确认 HTML ID |
| 相对路径404 | 2 | 统一用绝对路径 /static/... |
| DOMContentLoaded时序 | 2 | 用 readyState === loading 判断 |

---

## 🚫 防坑指南

### 1. JS 内联代码高危
提交前提取 JS 并验证语法：node --check static/js/*.js

### 2. DOMContentLoaded 不可靠
脚本在 body 底部时事件已触发，正确模式：
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

### 3. 资源路径一律绝对
静态资源：/static/css/style.css
导航链接：/index.html、/scan.html

### 4. 版本号单一源头
HTML: <span id="app-version"></span>
JS: fetch('/health') 动态加载
后端: APP_VERSION = "0.8.1"

---

## 📁 项目结构
/root/network-discovery/
├── app/main.py              # FastAPI 入口
├── app/models.py            # PortInfo 含 version 字段
├── app/services/scanner.py  # save_assets_to_db 存完整端口对象
├── static/js/app.js         # initApp 统一初始化
├── data/network.db          # SQLite 数据库
├── index.html, scan.html, assets.html, asset_detail.html

环境配置：
- 服务器: 192.168.88.94 (RockyLinux 9.7)
- 服务: Systemd network-discovery.service → Uvicorn 4 workers :8000
- Nginx: 80 → 反向代理到 127.0.0.1:8000
