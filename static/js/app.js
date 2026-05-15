/*
 * 网络设备发现平台 - JavaScript入口文件
 * 版本: 动态加载
 * 功能: 真实数据绑定 + 扫描进度跟踪 + Chart.js 图表
 */

// ===== Toast 提示系统 (v0.9.7 fix2) =====
// 必须在文件开头定义，确保全局可用
function showToast(message, type) {
    type = type || 'info';
    var container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        // 直接设置样式确保不被覆盖
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 8px;';
        document.body.appendChild(container);
    }
    // 确保容器可见
    container.style.display = 'flex';

    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;

    var icon = type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️';
    toast.innerHTML = '<span>' + icon + '</span><span>' + message + '</span>';

    container.appendChild(toast);

    // 强制重绘，确保动画生效
    toast.offsetHeight;
    toast.classList.add('toast-show');

    // 3秒后淡出移除
    setTimeout(function() {
        toast.classList.remove('toast-show');
        toast.classList.add('toast-hide');
        setTimeout(function() {
            toast.remove();
            // 容器为空时隐藏，但不删除
            if (container.children.length === 0) {
                container.style.display = 'none';
            }
        }, 300);
    }, 3000);
}

// ===== 按钮 Loading 状态 =====
function setButtonLoading(btn, loading) {
    if (loading) {
        btn.disabled = true;
        btn.classList.add('btn-loading');
        btn.dataset.originalText = btn.textContent;
        btn.textContent = '扫描中...';
    } else {
        btn.disabled = false;
        btn.classList.remove('btn-loading');
        btn.textContent = btn.dataset.originalText || '开始扫描';
    }
}

// 图表实例
var statusChart = null;
var vendorChart = null;

// 深色主题配色
var chartColors = {
    online: '#27ae60',
    offline: '#e74c3c',
    unknown: '#6b7280',
    primary: '#00d4ff',
    secondary: '#8e44ad',
    tertiary: '#f39c12',
    quaternary: '#1abc9c',
    quinary: '#3498db'
};

// ===== 统一初始化函数 =====
async function initApp() {
    console.log("Network Discovery Platform UI initializing...");

    // 1. 加载版本号
    var versionEl = document.getElementById('app-version');
    if (versionEl) {
        try {
            var res = await fetch('/health');
            var data = await res.json();
            versionEl.textContent = 'v' + data.version;
            console.log('Version loaded:', data.version);
        } catch (e) {
            versionEl.textContent = 'v?.?.?';
            console.error('Failed to load version:', e);
        }
    }

    // 2. 加载仪表盘统计数据
    await loadDashboardStats();

    // 3. 启动扫描进度跟踪（如果扫描页面）
    if (window.location.pathname.includes('scan')) {
        startScanProgressTracking();
    }
}

// ===== 仪表盘统计 =====
async function loadDashboardStats() {
    var statsContainer = document.getElementById('stat-total-ip');
    if (!statsContainer) return;

    try {
        var response = await fetch('/api/assets/?page=1&page_size=100');
        if (!response.ok) return;

        var data = await response.json();
        var total = data.total || 0;

        // 计算在线/离线/未知
        var online = 0, offline = 0, unknown = 0;
        var vendorStats = {};

        data.assets.forEach(function(asset) {
            if (asset.status === 'up' || asset.status === 'online') online++;
            else if (asset.status === 'down' || asset.status === 'offline') offline++;
            else unknown++;

            var key = asset.vendor || asset.os_name || '未知';
            if (key.trim() === '') key = asset.os_name || '未知';
            vendorStats[key] = (vendorStats[key] || 0) + 1;
        });

        updateStatCard('stat-total-ip', total);
        updateStatCard('stat-online-ip', online);
        updateStatCard('stat-offline-ip', offline);
        updateStatCard('stat-unknown-ip', unknown);

        console.log('Dashboard stats loaded:', {total: total, online: online, offline: offline, unknown: unknown});

        updateCharts(online, offline, unknown, vendorStats);

        // 加载最近扫描记录
        await loadRecentScans();

    } catch (e) {
        console.error('Failed to load dashboard stats:', e);
        showChartFallback();
    }
}

// ===== 最近扫描记录 =====
async function loadRecentScans() {
    var container = document.getElementById('recent-scans-list');
    if (!container) return;

    try {
        var response = await fetch('/api/scan/tasks');
        var data = await response.json();

        var tasks = data.tasks || [];
        if (tasks.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-secondary);">暂无扫描记录</div>';
            return;
        }

        // 取最近5条，按时间倒序
        var recent = tasks.slice(0, 5);

        var html = recent.map(function(task) {
            var time = new Date(task.created_at);
            var timeStr = time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            var statusIcon = task.status === 'completed' ? '✅' :
                            task.status === 'running' || task.status === 'scanning' ? '🔵' :
                            task.status === 'queued' || task.status === 'pending' ? '🟡' : '❌';
            var statusText = task.status === 'completed' ? '完成' :
                            task.status === 'running' || task.status === 'scanning' ? '运行' :
                            task.status === 'queued' || task.status === 'pending' ? '排队' : '失败';
            return '<div class="scan-record-item">' +
                '<span class="scan-time">' + timeStr + '</span>' +
                '<span class="scan-target">' + task.target + '</span>' +
                '<span class="scan-status">' + statusIcon + ' ' + statusText + '</span>' +
            '</div>';
        }).join('');

        container.innerHTML = html;

    } catch (e) {
        console.error('Failed to load recent scans:', e);
        container.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-secondary);">加载失败</div>';
    }
}

function updateStatCard(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
}

// ===== 图表渲染 =====
function updateCharts(online, offline, unknown, vendorStats) {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded');
        showChartFallback();
        return;
    }

    var statusCanvas = document.getElementById('chart-status');
    var vendorCanvas = document.getElementById('chart-vendor');

    if (!statusCanvas || !vendorCanvas) return;

    var statusCtx = statusCanvas.getContext('2d');
    if (statusChart) {
        statusChart.destroy();
    }
    statusChart = new Chart(statusCtx, {
        type: 'doughnut',
        data: {
            labels: ['在线', '离线', '未知'],
            datasets: [{
                data: [online, offline, unknown],
                backgroundColor: [chartColors.online, chartColors.offline, chartColors.unknown],
                borderColor: '#1e2d3d',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#b8c5d6',
                        padding: 20,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            var total = context.dataset.data.reduce(function(a, b) { return a + b; }, 0);
                            var percentage = total > 0 ? Math.round((context.raw / total) * 100) : 0;
                            return context.label + ': ' + context.raw + ' (' + percentage + '%)';
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });

    var vendorCtx = vendorCanvas.getContext('2d');
    if (vendorChart) {
        vendorChart.destroy();
    }

    var sortedVendors = Object.entries(vendorStats)
        .sort(function(a, b) { return b[1] - a[1]; })
        .slice(0, 5);

    var vendorLabels = sortedVendors.map(function(item) { return item[0]; });
    var vendorData = sortedVendors.map(function(item) { return item[1]; });
    var vendorColors = [chartColors.primary, chartColors.secondary, chartColors.tertiary, chartColors.quaternary, chartColors.quinary];

    vendorChart = new Chart(vendorCtx, {
        type: 'bar',
        data: {
            labels: vendorLabels,
            datasets: [{
                label: '数量',
                data: vendorData,
                backgroundColor: vendorColors,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '数量: ' + context.raw;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#b8c5d6', maxRotation: 45, minRotation: 0 }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#b8c5d6', stepSize: 1 },
                    beginAtZero: true
                }
            }
        }
    });

    console.log('Charts updated');
}

function showChartFallback() {
    var statusFallback = document.getElementById('chart-status-fallback');
    var vendorFallback = document.getElementById('chart-vendor-fallback');
    if (statusFallback) statusFallback.style.display = 'block';
    if (vendorFallback) vendorFallback.style.display = 'block';
}

// ===== 扫描进度跟踪 =====
function startScanProgressTracking() {
    var pollInterval = 3000;

    async function checkScanStatus() {
        try {
            var response = await fetch('/api/scan/tasks');
            var data = await response.json();
            var activeScan = data.tasks.find(function(t) { return t.status === 'scanning'; });

            if (activeScan) {
                updateScanProgress(activeScan);
            }
        } catch (e) {
            console.error('Failed to check scan status:', e);
        }
    }

    setInterval(checkScanStatus, pollInterval);
}

function updateScanProgress(task) {
    var statusEl = document.getElementById('scan-status');
    if (statusEl) {
        statusEl.textContent = task.status;
        statusEl.className = 'status-badge ' + (task.status === 'completed' ? 'online' : 'scanning');
    }
}

// ===== 执行初始化 =====
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}