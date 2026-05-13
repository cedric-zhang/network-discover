/*
 * 网络设备发现平台 - JavaScript入口文件
 *
 * 注意：此版本为UI骨架阶段，不包含实际功能
 * 预留 HTMX/Vue 接入点，但暂不实现具体逻辑
 */

// TODO: [预留] HTMX/Vue 接入点
// 在后续开发中，这里将接入动态数据绑定和交互逻辑

document.addEventListener('DOMContentLoaded', function() {
    console.log('Network Discovery Platform UI v0.2.0');

    // TODO: [预留] 页面加载后的初始化逻辑
    // 在后端接口完成后，此处将初始化数据绑定和事件监听

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

        try {
            const response = await fetch('/api/scan/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    target: target,
                    scan_options: scanOptions,
                    schedule: document.querySelector('.select')?.value || 'now'
                })
            });

            const result = await response.json();

            if (response.ok) {
                alert(result.message || '扫描任务已提交');
            } else {
                alert(`提交失败: ${result.detail || '未知错误'}`);
            }
        } catch (error) {
            console.error('提交扫描任务时出错:', error);
            alert('提交失败，请检查网络连接');
        }
    });

    // 为"开始扫描"按钮添加事件（如果它是按钮而非表单提交）
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

        try {
            const response = await fetch('/api/scan/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    target: target,
                    scan_options: {
                        port_scan: true,
                        os_detection: true,
                        vendor_detection: true
                    },
                    schedule: 'now'
                })
            });

            const result = await response.json();

            if (response.ok) {
                alert(result.message || '扫描任务已提交');
            } else {
                alert(`提交失败: ${result.detail || '未知错误'}`);
            }
        } catch (error) {
            console.error('提交扫描任务时出错:', error);
            alert('提交失败，请检查网络连接');
        }
    });
});