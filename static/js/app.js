/*
 * 网络设备发现平台 - JavaScript入口文件
 * 版本: v0.8.1
 * 功能: 真实数据绑定 + 扫描进度跟踪
 */

// Version loading function - handles both DOM loading and already loaded states
async function loadVersion() {
    const el = document.getElementById('app-version');
    if (!el) {
        console.warn('app-version element not found');
        return;
    }
    try {
        const res = await fetch('/health');
        const data = await res.json();
        el.textContent = 'v' + data.version;
        console.log('Version loaded:', data.version);
    } catch (e) {
        el.textContent = 'v?.?.?';
        console.error('Failed to load version:', e);
    }
}

// Execute version loading immediately or on DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadVersion);
} else {
    loadVersion();  // DOM already loaded, execute directly
}

document.addEventListener('DOMContentLoaded', async function() {
    console.log('Network Discovery Platform UI v0.8.1');

    // 加载仪表盘统计数据（根据现有API计算）
    async function loadDashboardStats() {
        try {
            // 获取扫描任务数据并计算统计信息
            const response = await fetch('/api/scan/tasks');
            if (response.ok) {
                const data = await response.json();
                const tasks = data.tasks || [];

                // 计算统计信息
                let totalIps = 0;
                let onlineCount = 0;
                let offlineCount = 0;
                let unknownCount = 0;

                // 根据现有任务计算粗略统计
                for (const task of tasks) {
                    if (task.total_hosts) {
                        totalIps += task.total_hosts;
                    }

                    // 根据任务状态进行分类（简单实现）
                    if (task.status === 'completed' && task.scanned_hosts > 0) {
                        onlineCount += Math.min(task.scanned_hosts, 1); // 至少1个在线
                    } else if (task.status === 'failed') {
                        offlineCount++;
                    } else {
                        unknownCount++;
                    }
                }

                // 更新统计卡片
                document.getElementById('stat-total-ip')?.textContent = totalIps || 0;
                document.getElementById('stat-online-ip')?.textContent = onlineCount || 0;
                document.getElementById('stat-offline-ip')?.textContent = offlineCount || 0;
                document.getElementById('stat-unknown-ip')?.textContent = unknownCount || 0;
            } else {
                console.warn('Failed to load scan tasks');
            }
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
        }
    }

    // 加载最近扫描记录
    async function loadRecentScans() {
        try {
            const response = await fetch('/api/scan/tasks');
            if (response.ok) {
                const data = await response.json();
                const container = document.getElementById('recent-scans-list');

                if (container && data.tasks && data.tasks.length > 0) {
                    // 取最近的5个任务
                    const recentTasks = data.tasks.slice(0, 5);
                    const scanListHtml = recentTasks.map(task => `
                        <div class="scan-item" style="padding: 8px 0; border-bottom: 1px solid var(--border); margin-bottom: 8px;">
                            <div><strong>${task.target || task.task_id}</strong></div>
                            <div style="font-size: 0.9em; color: var(--text-secondary);">
                                状态: ${task.status || 'unknown'} | 进度: ${task.progress || 0}%
                            </div>
                            <div style="font-size: 0.8em; color: var(--text-tertiary);">
                                ${new Date(task.created_at || task.updated_at).toLocaleString()}
                            </div>
                        </div>
                    `).join('');
                    container.innerHTML = scanListHtml;
                } else if (container) {
                    container.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-secondary);">暂无扫描记录</div>';
                }
            }
        } catch (error) {
            console.error('Error loading recent scans:', error);
        }
    }

    // 加载资产列表
    async function loadAssetList() {
        try {
            // 由于资产API可能尚未实现，我们暂时使用扫描任务中的数据
            const response = await fetch('/api/scan/tasks?skip=0&limit=10');
            if (response.ok) {
                const data = await response.json();

                // 更新资产统计
                document.getElementById('assets-count')?.textContent = `已发现 ${data.total || 0} 个 IP 地址`;

                // 如果在资产页面，可以加载详细列表
                if (window.location.pathname.includes('assets.html')) {
                    const tbody = document.querySelector('tbody');
                    if (tbody && data.tasks && data.tasks.length > 0) {
                        const assetsHtml = data.tasks.map(task => `
                            <tr>
                                <td>${task.target || task.task_id}</td>
                                <td><span class="status ${getStatusClass(task.status || 'unknown')}">${task.status || 'unknown'}</span></td>
                                <td>${task.target || '-'}</td>
                                <td>-</td>
                                <td>-</td>
                                <td>-</td>
                                <td>${task.updated_at ? new Date(task.updated_at).toLocaleDateString() : '-'}</td>
                            </tr>
                        `).join('');
                        tbody.innerHTML = assetsHtml;
                    } else if (tbody) {
                        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px;">暂无资产数据</td></tr>';
                    }
                }
            }
        } catch (error) {
            console.error('Error loading asset list:', error);
        }
    }

    // 获取状态样式类
    function getStatusClass(status) {
        switch (status.toLowerCase()) {
            case 'online':
            case 'completed':
                return 'status-online';
            case 'offline':
            case 'failed':
                return 'status-offline';
            case 'scanning':
            case 'pending':
                return 'status-pending';
            case 'unknown':
            default:
                return 'status-unknown';
        }
    }

    // 轮询扫描任务状态
    async function pollScanStatus(taskId) {
        const statusElement = document.getElementById(`task-${taskId}-status`);
        const progressElement = document.getElementById(`task-${taskId}-progress`);

        const poll = async () => {
            try {
                const response = await fetch(`/api/scan/tasks/${taskId}`);
                if (response.ok) {
                    const data = await response.json();

                    if (statusElement) {
                        statusElement.textContent = data.status;
                        statusElement.className = `status ${getStatusClass(data.status)}`;
                    }

                    // 使用正确的进度字段名
                    const progress = data.progress !== undefined ? data.progress : (data.scanned_hosts && data.total_hosts ? Math.round((data.scanned_hosts / data.total_hosts) * 100) : 0);
                    const totalHosts = data.total_hosts || 0;
                    const scannedHosts = data.scanned_hosts || 0;

                    if (progressElement) {
                        progressElement.textContent = `${progress}% (${scannedHosts}/${totalHosts})`;

                        // 根据进度更新颜色
                        if (progress === 100) {
                            progressElement.style.color = 'var(--accent-green)';
                        } else if (progress > 0) {
                            progressElement.style.color = 'var(--accent-blue)';
                        }
                    }

                    // 如果任务未完成，继续轮询
                    if (data.status !== 'completed' && data.status !== 'failed') {
                        setTimeout(poll, 2000); // 每2秒刷新一次
                    }
                }
            } catch (error) {
                console.error('Error polling scan status:', error);
                setTimeout(poll, 5000); // 出错时5秒后重试
            }
        };

        poll();
    }

    // 提交扫描任务
    async function submitScanTask(target, scanOptions) {
        try {
            const response = await fetch('/api/scan/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    target: target,
                    scan_options: scanOptions
                })
            });

            const result = await response.json();

            if (response.ok) {
                alert(result.message || '扫描任务已提交');

                // 如果是在扫描页面，显示任务状态
                if (result.task_id && window.location.pathname.includes('scan.html')) {
                    // 显示任务信息和进度
                    const taskInfoDiv = document.createElement('div');
                    taskInfoDiv.innerHTML = `
                        <div class="card" style="margin-top: 20px;">
                            <h3>扫描任务信息</h3>
                            <p><strong>任务ID:</strong> ${result.task_id}</p>
                            <p><strong>目标:</strong> ${result.target}</p>
                            <p><strong>状态:</strong> <span id="task-${result.task_id}-status" class="status status-pending">pending</span></p>
                            <p><strong>进度:</strong> <span id="task-${result.task_id}-progress">0% (0/0)</span></p>
                        </div>
                    `;
                    document.querySelector('.page-content')?.appendChild(taskInfoDiv);

                    // 开始轮询任务状态
                    pollScanStatus(result.task_id);
                }

                // 刷新仪表盘和扫描历史
                if (typeof loadDashboardStats === 'function') loadDashboardStats();
                if (typeof loadRecentScans === 'function') loadRecentScans();

                return result;
            } else {
                alert(`提交失败: ${result.detail || '未知错误'}`);
                return null;
            }
        } catch (error) {
            console.error('提交扫描任务时出错:', error);
            alert('提交失败，请检查网络连接');
            return null;
        }
    }

    // 连接后端API：扫描表单提交
    document.querySelector('.scan-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();

        const targetInput = document.getElementById('scan-target') || document.querySelector('input[type="text"]');
        if (!targetInput) {
            alert('未找到扫描目标输入框');
            return;
        }

        const target = targetInput.value.trim();
        if (!target) {
            alert('请输入扫描目标');
            return;
        }

        const scanOptions = {
            port_scan: document.querySelector('input[name="portScan"]')?.checked ?? true,
            os_detection: document.querySelector('input[name="osDetect"]')?.checked ?? true,
            vendor_detection: document.querySelector('input[name="vendorDetect"]')?.checked ?? true
        };

        await submitScanTask(target, scanOptions);
    });

    // 为"开始扫描"按钮添加事件
    document.querySelector('.btn-primary')?.addEventListener('click', async (e) => {
        // 避免重复处理表单提交事件
        if (e.target.closest('form')) {
            return; // 由表单提交事件处理
        }

        // 如果是独立按钮，获取页面上的第一个输入框作为目标
        const targetInput = document.getElementById('scan-target') || document.querySelector('input[type="text"]');
        if (!targetInput) {
            alert('未找到扫描目标输入框');
            return;
        }

        const target = targetInput.value.trim();
        if (!target) {
            alert('请输入扫描目标');
            return;
        }

        const scanOptions = {
            port_scan: true,
            os_detection: true,
            vendor_detection: true
        };

        await submitScanTask(target, scanOptions);
    });

    // 页面特定加载逻辑
    if (window.location.pathname.includes('index.html') || window.location.pathname === '/') {
        // 仪表盘页面加载数据
        loadDashboardStats();
        loadRecentScans();
        setInterval(() => {
            loadDashboardStats();
            loadRecentScans();
        }, 30000); // 每30秒刷新一次
    } else if (window.location.pathname.includes('assets.html')) {
        // 资产页面加载数据
        loadAssetList();
    } else if (window.location.pathname.includes('scan.html')) {
        // 扫描页面可以定期检查任务状态
        setInterval(() => {
            if (typeof loadRecentScans === 'function') loadRecentScans();
        }, 5000);
    }
});