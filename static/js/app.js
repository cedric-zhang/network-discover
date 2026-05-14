/*
 * 网络设备发现平台 - JavaScript入口文件
 * 版本: v0.8.1
 * 功能: 真实数据绑定 + 扫描进度跟踪
 */

// ===== 统一初始化函数 =====
async function initApp() {
    console.log('Network Discovery Platform UI v0.8.1 initializing...');
    
    // 1. 加载版本号
    const versionEl = document.getElementById('app-version');
    if (versionEl) {
        try {
            const res = await fetch('/health');
            const data = await res.json();
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
    const statsContainer = document.getElementById('stat-total-ip');
    if (!statsContainer) return; // 只在仪表盘页面执行
    
    try {
        const response = await fetch('/api/assets/?page=1&page_size=100');
        if (!response.ok) return;
        
        const data = await response.json();
        const total = data.total || 0;
        
        // 计算在线/离线/未知
        let online = 0, offline = 0, unknown = 0;
        data.assets.forEach(asset => {
            if (asset.status === 'up' || asset.status === 'online') online++;
            else if (asset.status === 'down' || asset.status === 'offline') offline++;
            else unknown++;
        });

        // 更新统计卡片
        updateStatCard('stat-total-ip', total);
        updateStatCard('stat-online-ip', online);
        updateStatCard('stat-offline-ip', offline);
        updateStatCard('stat-unknown-ip', unknown);
        
        console.log('Dashboard stats loaded:', {total, online, offline, unknown});
    } catch (e) {
        console.error('Failed to load dashboard stats:', e);
    }
}

function updateStatCard(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

// ===== 扫描进度跟踪 =====
function startScanProgressTracking() {
    // 检查是否有进行中的扫描
    const pollInterval = 3000;
    
    async function checkScanStatus() {
        try {
            const response = await fetch('/api/scan/tasks');
            const data = await response.json();
            const activeScan = data.tasks.find(t => t.status === 'scanning');
            
            if (activeScan) {
                updateScanProgress(activeScan);
            }
        } catch (e) {
            console.error('Failed to check scan status:', e);
        }
    }
    
    // 每 3 秒检查一次
    setInterval(checkScanStatus, pollInterval);
}

function updateScanProgress(task) {
    const statusEl = document.getElementById('scan-status');
    if (statusEl) {
        statusEl.textContent = task.status;
        statusEl.className = 'status-badge ' + (task.status === 'completed' ? 'online' : 'scanning');
    }
}

// ===== 执行初始化 =====
// 兼容处理：如果文档已加载完直接执行，否则等待加载
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();  // DOM 已加载，立即执行
}
