// PCB工程资料管理系统 - 主JavaScript文件

// 简单的 HTML 转义函数，防止 XSS
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

// CSRF Token获取
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// API请求封装
const api = {
    get: async (url, params = {}) => {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        try {
            const response = await fetch(fullUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            if (!response.ok) {
                console.error('API GET 错误:', response.status, fullUrl);
                return { error: `请求失败 (${response.status})` };
            }
            return response.json();
        } catch (err) {
            console.error('API GET 异常:', err);
            return { error: '网络请求失败，请检查连接' };
        }
    },
    
    post: async (url, data = {}) => {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                console.error('API POST 错误:', response.status, url);
                return { error: `请求失败 (${response.status})` };
            }
            return response.json();
        } catch (err) {
            console.error('API POST 异常:', err);
            return { error: '网络请求失败，请检查连接' };
        }
    },
    
    put: async (url, data = {}) => {
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                console.error('API PUT 错误:', response.status, url);
                return { error: `请求失败 (${response.status})` };
            }
            return response.json();
        } catch (err) {
            console.error('API PUT 异常:', err);
            return { error: '网络请求失败，请检查连接' };
        }
    },
    
    delete: async (url) => {
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            if (!response.ok) {
                console.error('API DELETE 错误:', response.status, url);
                return { error: `请求失败 (${response.status})` };
            }
            return response.json();
        } catch (err) {
            console.error('API DELETE 异常:', err);
            return { error: '网络请求失败，请检查连接' };
        }
    }
};

// 显示加载中
function showLoading(message = '加载中...') {
    if (!document.getElementById('globalLoading')) {
        const loading = document.createElement('div');
        loading.id = 'globalLoading';
        loading.className = 'loading-overlay';
        loading.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary mb-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="text-muted">${message}</div>
            </div>
        `;
        document.body.appendChild(loading);
    }
}

// 隐藏加载中
function hideLoading() {
    const loading = document.getElementById('globalLoading');
    if (loading) {
        loading.remove();
    }
}

// 显示消息
function showMessage(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// 确认对话框
function confirmDialog(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 格式化日期
function formatDate(dateString, format = 'YYYY-MM-DD HH:mm:ss') {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 获取状态颜色
function getStatusColor(status) {
    const colors = {
        'draft': 'secondary',
        'pending': 'warning',
        'approved': 'primary',
        'rejected': 'danger',
        'published': 'success',
        'archived': 'info',
        'running': 'primary',
        'completed': 'success',
        'failed': 'danger',
        'cancelled': 'secondary'
    };
    return colors[status] || 'secondary';
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 初始化DataTable
function initDataTable(selector, options = {}) {
    const defaultOptions = {
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/zh.json'
        },
        pageLength: 20,
        ordering: true,
        searching: true,
        responsive: true
    };
    
    return $(selector).DataTable({...defaultOptions, ...options});
}

// 导出表格数据
function exportTableData(selector, filename, format = 'excel') {
    const table = document.querySelector(selector);
    if (!table) return;
    
    if (format === 'excel') {
        // 使用SheetJS导出Excel
        const wb = XLSX.utils.table_to_book(table);
        XLSX.writeFile(wb, `${filename}.xlsx`);
    } else if (format === 'csv') {
        const wb = XLSX.utils.table_to_book(table);
        XLSX.writeFile(wb, `${filename}.csv`);
    }
}

// 初始化工具提示
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 初始化弹出框
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化Bootstrap组件
    initTooltips();
    initPopovers();
    
    // 添加淡入动画
    document.querySelectorAll('.card, .stat-card').forEach(el => {
        el.classList.add('fade-in');
    });
});

// 全局错误处理
window.onerror = function(message, source, lineno, colno, error) {
    console.error('全局错误:', {message, source, lineno, colno, error});
    showMessage('发生错误，请刷新页面重试', 'danger');
    return false;
};

// 未处理的Promise错误
window.addEventListener('unhandledrejection', function(event) {
    console.error('未处理的Promise错误:', event.reason);
    showMessage('请求失败，请检查网络连接', 'warning');
});
