# 网络设备发现平台 · Claude Code 开发上下文

> **最后更新**: 2026-05-15 | **当前版本**: v0.9.4 | **状态**: 已发布 (扫描交互反馈)

---

## 🚨 环境强制声明（不遵守 = 任务作废）

> **你的运行环境是本地开发机 (Windows)，但项目只在远程服务器上！**
> **📍 唯一合法的开发目录**: `192.168.88.94:/root/network-discovery`
> **🔑 唯一合法的操作方式**: 通过 `ssh root@192.168.88.94` 执行所有命令

---

## 📊 当前状态 (v0.9.4)

### ✅ v0.9.4 更新内容
*   **Toast 提示系统**: 成功/失败/警告三种样式，右上角滑入，3秒自动消失
*   **按钮 Loading 状态**: disabled + 旋转图标 + "扫描中..." 文案
*   **Placeholder 动态切换**: 网段扫描/单IP扫描自动切换提示
*   **扫描校验**: 空值/格式/超大网段校验，Toast 提示而非 alert

### ✅ 历史版本
*   **v0.9.3**: JS 版本动态化、Bento Grid 4列、扫描校验、空状态优化
*   **v0.9.2**: CSV 导出功能
*   **v0.9.1**: 仪表盘 Chart.js 图表
*   **v0.9.0**: 定时扫描配置、WAL 模式、扫描锁

### ⏭️ 下一步计划
*   **v0.10.0 候选**: Excel 导出、资产趋势图表、API 文档。

---

## 📁 项目结构
```
/root/network-discovery/
├── app/main.py           # version: 0.9.4
├── static/js/app.js      # showToast(), setButtonLoading()
├── static/css/style.css  # toast-container, btn-loading
├── scan.html             # 完整扫描反馈链路
```

---

## 🛠️ 开发规范

1. **Git 分支**: 在 `dev/*` 分支开发，完成后合并到 `main`
2. **Toast**: 禁止使用第三方库，纯 CSS/JS 实现
3. **禁止**: 进度条（nmap无标准输出）、弹窗/模态框
