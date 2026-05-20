/*
 * 网络设备发现平台 - JavaScript入口文件
 * 版本: v0.9.9-fix2
 * 功能: 真实数据绑定 + 扫描进度跟踪 + Chart.js 图表
 */

// ===== Toast 提示系统 (v0.9.9 CSS动画版) =====
function showToast(message, type) {
    type = type || "info";
    console.log("[Toast] Creating:", message, type);

    var container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        document.body.appendChild(container);
    }
    container.style.cssText = "position:fixed;top:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;";

    var bgColor = type === "success" ? "#10b981" : type === "error" ? "#ef4444" : type === "warning" ? "#f59e0b" : "#3b82f6";
    var icon = type === "success" ? "✅" : type === "error" ? "❌" : type === "warning" ? "⚠️" : "ℹ️";

    var toast = document.createElement("div");
    toast.className = "toast toast-" + type + " toast-auto-fade";
    toast.style.cssText = "padding:12px 20px;border-radius:12px;font-size:14px;color:#fff;background:" + bgColor + ";box-shadow:0 4px 12px rgba(0,0,0,0.3);display:flex;align-items:center;gap:8px;z-index:10000;opacity:1;";
    toast.innerHTML = "<span>" + icon + "</span><span>" + message + "</span>";

    container.appendChild(toast);
    console.log("[Toast] Appended with CSS animation (3s fade)");

    setTimeout(function cleanup() {
        toast.remove();
        if (container.children.length === 0) {
            container.style.display = "none";
        }
    }, 3500);
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
var osChart = null;

// 深色主题配色 - 状态颜色
var chartColors = {
    online: '#22c55e',
    offline: '#ef4444',
    unknown: '#6b7280',
    primary: '#00d4ff',
    secondary: '#8e44ad',
    tertiary: '#f59e0b',
    quaternary: '#1abc9c',
    quinary: '#3498db'
};

// 厂商颜色映射表 - 扩展更多厂商
var vendorColorMap = {
    'Cisco': '#3b82f6',           // 蓝
    'Huawei': '#ef4444',          // 红
    'H3C': '#10b981',             // 绿
    'Hangzhou H3C': '#10b981',    // 绿
    'Juniper': '#f59e0b',         // 黄
    'Dell': '#8b5cf6',            // 紫
    'HP': '#ec4899',              // 粉
    'Lenovo': '#06b6d4',          // 青
    'Intel': '#64748b',           // 灰蓝
    'AMD': '#f97316',             // 橙
    'VMware': '#7c3aed',          // 深紫
    'Ruijie Networks': '#14b8a6', // 青绿
    'Ruijie': '#14b8a6',          // 青绿
    'Broadcom': '#a855f7',        // 紫粉
    'Broadcom Limited': '#a855f7', // 紫粉
    'Wistron': '#84cc16',         // 黄绿
    'Wistron Infocomm': '#84cc16', // 黄绿
    'Apple': '#6b7280',           // 灰
    'Samsung': '#0369a1',         // 深蓝
    'Microsoft': '#059669',       // 深绿
    'Google': '#dc2626',          // 深红
    'Unknown': '#6b7280',         // 灰
    '未知': '#6b7280',
    'unknown': '#6b7280'
};

// OS颜色映射表 - 扩展更多系统
var osColorMap = {
    'Linux': '#10b981',           // 绿
    'Ubuntu': '#22c55e',          // 亮绿
    'CentOS': '#ef4444',          // 红
    'RedHat': '#dc2626',          // 深红
    'Debian': '#14b8a6',          // 青绿
    'Fedora': '#3b82f6',          // 蓝
    'Windows': '#3b82f6',         // 蓝
    'Windows Server': '#2563eb',  // 深蓝
    'macOS': '#8b5cf6',           // 紫
    'Darwin': '#a855f7',          // 紫粉
    'FreeBSD': '#06b6d4',         // 青
    'OpenBSD': '#0891b2',         // 深青
    'Android': '#22c55e',         // 绿
    'iOS': '#8b5cf6',             // 紫
    'ESXi': '#7c3aed',            // 深紫
    'VMware ESX': '#7c3aed',      // 深紫
    'Unknown': '#6b7280',         // 灰
    '未知': '#6b7280',
    'unknown': '#6b7280'
};

// 扩展颜色序列 - 20种独特颜色，确保不重复
var extendedColorSequence = [
    '#3b82f6',  // 蓝
    '#ef4444',  // 红
    '#10b981',  // 绿
    '#f59e0b',  // 黄
    '#8b5cf6',  // 紫
    '#06b6d4',  // 青
    '#ec4899',  // 粉
    '#f97316',  // 橙
    '#14b8a6',  // 青绿
    '#a855f7',  // 紫粉
    '#7c3aed',  // 深紫
    '#84cc16',  // 黄绿
    '#0ea5e9',  // 天蓝
    '#d946ef',  // 亮紫
    '#64748b',  // 灰蓝
    '#22c55e',  // 亮绿
    '#dc2626',  // 深红
    '#059669',  // 深绿
    '#2563eb',  // 深蓝
    '#0891b2'   // 深青
];

// 用于跟踪已分配颜色的厂商/OS
var assignedColors = {};

// 根据名称获取颜色（厂商或OS）- 确保每个类别独立颜色
function getColorForLabel(label, colorMap, colorSequence, index) {
    // 未知/unknown统一使用灰色
    if (label.toLowerCase().includes('unknown') || label.toLowerCase().includes('未知') || label.trim() === '') {
        return '#6b7280';
    }

    // 直接匹配
    if (colorMap[label]) {
        return colorMap[label];
    }

    // 部分匹配（如 "Linux 5.4" 匹配 Linux，"Hangzhou H3C" 匹配 H3C）
    for (var key in colorMap) {
        if (label.toLowerCase().includes(key.toLowerCase()) || key.toLowerCase().includes(label.toLowerCase())) {
            return colorMap[key];
        }
    }

    // 新发现的厂商/OS - 使用扩展颜色序列，按索引分配唯一颜色
    // 确保 "未知" 不占用颜色序列的位置
    var colorIndex = index % colorSequence.length;
    return colorSequence[colorIndex];
}

// ===== 统一初始化函数 =====
async function initApp() {
    console.log("Network Discovery Platform UI initializing...");

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

    await loadDashboardStats();

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

        var online = 0, offline = 0, unknown = 0;
        var vendorStats = {};
        var osStats = {};

        data.assets.forEach(function(asset) {
            if (asset.status === 'up' || asset.status === 'online') online++;
            else if (asset.status === 'down' || asset.status === 'offline') offline++;
            else unknown++;

            var vendorKey = asset.vendor || '未知';
            if (vendorKey.trim() === '') vendorKey = '未知';
            vendorStats[vendorKey] = (vendorStats[vendorKey] || 0) + 1;

            var osKey = asset.os_name || '未知';
            if (osKey.trim() === '') osKey = '未知';
            osStats[osKey] = (osStats[osKey] || 0) + 1;
        });

        updateStatCard('stat-total-ip', total);
        updateStatCard('stat-online-ip', online);
        updateStatCard('stat-offline-ip', offline);
        updateStatCard('stat-unknown-ip', unknown);

        console.log('Dashboard stats loaded:', {total: total, online: online, offline: offline, unknown: unknown});

        updateCharts(online, offline, unknown, vendorStats, osStats);

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
            var displayName = task.name || task.target;
            return '<div class="scan-record-item">' +
                '<span class="scan-time">' + timeStr + '</span>' +
                '<span class="scan-target">' + displayName + '</span>' +
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
function updateCharts(online, offline, unknown, vendorStats, osStats) {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded');
        showChartFallback();
        return;
    }

    var statusCanvas = document.getElementById('chart-status');
    var vendorCanvas = document.getElementById('chart-vendor');

    if (!statusCanvas || !vendorCanvas) return;

    // 1. 状态分布图（环形图）
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

    // 2. 厂商分布图（柱状图）- 每个厂商独立颜色
    var vendorCtx = vendorCanvas.getContext('2d');
    if (vendorChart) {
        vendorChart.destroy();
    }

    var sortedVendors = Object.entries(vendorStats)
        .sort(function(a, b) { return b[1] - a[1]; })
        .slice(0, 10);

    var vendorLabels = sortedVendors.map(function(item) { return item[0]; });
    var vendorData = sortedVendors.map(function(item) { return item[1]; });

    // 每个厂商分配独立颜色，使用索引确保不重复
    var vendorColors = vendorLabels.map(function(label, index) {
        return getColorForLabel(label, vendorColorMap, extendedColorSequence, index);
    });

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

    // 3. OS分布图（如果存在）
    var osCanvas = document.getElementById('chart-os');
    if (osCanvas) {
        var osCtx = osCanvas.getContext('2d');
        if (osChart) {
            osChart.destroy();
        }

        var sortedOS = Object.entries(osStats)
            .sort(function(a, b) { return b[1] - a[1]; })
            .slice(0, 10);

        var osLabels = sortedOS.map(function(item) { return item[0]; });
        var osData = sortedOS.map(function(item) { return item[1]; });

        // 每个OS分配独立颜色
        var osColors = osLabels.map(function(label, index) {
            return getColorForLabel(label, osColorMap, extendedColorSequence, index);
        });

        osChart = new Chart(osCtx, {
            type: 'bar',
            data: {
                labels: osLabels,
                datasets: [{
                    label: '数量',
                    data: osData,
                    backgroundColor: osColors,
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
    }

    console.log('Charts updated - each vendor/OS has unique color');
}

function showChartFallback() {
    var statusFallback = document.getElementById('chart-status-fallback');
    var vendorFallback = document.getElementById('chart-vendor-fallback');
    if (statusFallback) statusFallback.style.display = 'block';
    if (vendorFallback) vendorFallback.style.display = 'block';
}

// ===== 扫描进度跟踪 =====
function startScanProgressTracking() {
    // Track last submitted scan task for progress
    var pollInterval = 3000;

    async function checkScanStatus() {
        try {
            var response = await fetch('/api/scan/tasks?page=1&page_size=3');
            var data = await response.json();
            if (!data.tasks || data.tasks.length === 0) return;

            var activeScan = data.tasks.find(function(t) {
                return t.status === 'scanning' || t.status === 'running';
            });

            if (activeScan && activeScan.task_id) {
                updateScanProgress(activeScan);
            }
        } catch (e) {
            console.error('Progress check failed:', e);
        }
    }

    setInterval(checkScanStatus, pollInterval);
}

function updateScanProgress(task) {
    var area = document.getElementById('scan-progress-area');
    if (!area) return;

    // Progress shown in tasks.html, not scan page;

    var pctEl = document.getElementById('scan-progress-pct');
    var barEl = document.getElementById('scan-progress-bar');
    var textEl = document.getElementById('scan-progress-text');
    var detailEl = document.getElementById('scan-progress-detail');

    var progress = task.progress || 0;
    var currentIp = task.current_ip || '';
    var totalIps = task.total_ips || 0;
    var elapsed = task.elapsed_seconds || 0;

    if (pctEl) pctEl.textContent = progress + '%';
    if (barEl) barEl.style.width = (progress > 0 ? progress : 5) + '%';

    if (task.status === 'completed') {
        if (textEl) textEl.textContent = '扫描完成';
        if (pctEl) pctEl.textContent = '100%';
        if (barEl) barEl.style.width = '100%';
        if (detailEl) detailEl.textContent = '已发现主机';
        setTimeout(function() { if (area) area.style.display = 'none'; }, 5000);
    } else if (task.status === 'failed') {
        if (textEl) textEl.textContent = '扫描失败';
        if (detailEl) detailEl.textContent = task.message || task.error || '未知错误';
        setTimeout(function() { if (area) area.style.display = 'none'; }, 10000);
    } else {
        var statusText = '扫描中...';
        if (currentIp) statusText += ' 当前: ' + currentIp;
        if (textEl) textEl.textContent = statusText;

        var detail = '';
        if (totalIps > 0) detail += '共 ' + totalIps + ' 个IP';
        if (elapsed > 0) detail += ' | 已用时 ' + Math.round(elapsed) + '秒';
        if (detailEl) detailEl.textContent = detail;
    }
}

// ===== 执行初始化 =====
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}