/*
 * 网络设备发现平台 - JavaScript入口文件
 * 版本: v0.9.9-fix1
 * 功能: 真实数据绑定 + 扫描进度跟踪 + Chart.js 图表
 */

// ===== Toast 提示系统 (v0.9.9 CSS动画版) =====
// 使用 CSS animation 控制消失，不依赖 setTimeout
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

    // 仅用于清理 DOM，动画结束后移除元素
    setTimeout(function cleanup() {
        toast.remove();
        if (container.children.length === 0) {
            container.style.display = "none";
        }
    }, 3500); // 比 animation 久一点
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
    online: '#22c55e',     // 绿色 - 在线
    offline: '#ef4444',    // 红色 - 离线
    unknown: '#6b7280',    // 灰色 - 未知
    primary: '#00d4ff',    // 青色 - 主色
    secondary: '#8e44ad',  // 紫色
    tertiary: '#f59e0b',   // 黄色
    quaternary: '#1abc9c', // 青绿
    quinary: '#3498db'     // 蓝色
};

// 厂商颜色映射表 - 不同厂商用不同颜色
var vendorColorMap = {
    'Cisco': '#3b82f6',       // 蓝
    'Huawei': '#ef4444',      // 红
    'H3C': '#10b981',         // 绿
    'Juniper': '#f59e0b',     // 黄
    'Dell': '#8b5cf6',        // 紫
    'HP': '#ec4899',          // 粉
    'Lenovo': '#06b6d4',      // 青
    'Intel': '#64748b',       // 灰蓝
    'AMD': '#f97316',         // 橙
    'Unknown': '#6b7280',     // 灰
    '未知': '#6b7280',        // 灰
    'unknown': '#6b7280'      // 灰
};

// OS颜色映射表 - 不同系统用不同颜色
var osColorMap = {
    'Linux': '#10b981',       // 绿
    'Ubuntu': '#10b981',      // 绿
    'CentOS': '#10b981',      // 绿
    'RedHat': '#ef4444',      // 红
    'Debian': '#10b981',      // 绿
    'Windows': '#3b82f6',     // 蓝
    'Windows Server': '#3b82f6', // 蓝
    'macOS': '#8b5cf6',       // 紫
    'Darwin': '#8b5cf6',      // 紫
    'FreeBSD': '#06b6d4',     // 青
    'Android': '#22c55e',     // 绿
    'iOS': '#8b5cf6',         // 紫
    'Unknown': '#6b7280',     // 灰
    '未知': '#6b7280',        // 灰
    'unknown': '#6b7280'      // 灰
};

// 默认颜色序列（用于未知厂商/OS）
var defaultColorSequence = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#64748b'];

// 根据名称获取颜色（厂商或OS）
function getColorForLabel(label, colorMap) {
    // 直接匹配
    if (colorMap[label]) {
        return colorMap[label];
    }
    // 部分匹配（如 "Linux 5.4" 匹配 Linux）
    for (var key in colorMap) {
        if (label.toLowerCase().includes(key.toLowerCase())) {
            return colorMap[key];
        }
    }
    // 未知/unknown匹配
    if (label.toLowerCase().includes('unknown') || label.toLowerCase().includes('未知')) {
        return '#6b7280';
    }
    // 返回默认序列中的颜色（按索引轮换）
    var index = Object.keys(colorMap).length % defaultColorSequence.length;
    return defaultColorSequence[index];
}

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
        var osStats = {};

        data.assets.forEach(function(asset) {
            if (asset.status === 'up' || asset.status === 'online') online++;
            else if (asset.status === 'down' || asset.status === 'offline') offline++;
            else unknown++;

            // 统计厂商
            var vendorKey = asset.vendor || '未知';
            if (vendorKey.trim() === '') vendorKey = '未知';
            vendorStats[vendorKey] = (vendorStats[vendorKey] || 0) + 1;

            // 统计OS
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

    // 2. 厂商分布图（柱状图）- 使用厂商颜色映射
    var vendorCtx = vendorCanvas.getContext('2d');
    if (vendorChart) {
        vendorChart.destroy();
    }

    var sortedVendors = Object.entries(vendorStats)
        .sort(function(a, b) { return b[1] - a[1]; })
        .slice(0, 6);

    var vendorLabels = sortedVendors.map(function(item) { return item[0]; });
    var vendorData = sortedVendors.map(function(item) { return item[1]; });
    // 根据厂商名称分配颜色
    var vendorColors = vendorLabels.map(function(label) {
        return getColorForLabel(label, vendorColorMap);
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
            .slice(0, 6);

        var osLabels = sortedOS.map(function(item) { return item[0]; });
        var osData = sortedOS.map(function(item) { return item[1]; });
        // 根据OS名称分配颜色
        var osColors = osLabels.map(function(label) {
            return getColorForLabel(label, osColorMap);
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

    console.log('Charts updated with vendor/OS color mapping');
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