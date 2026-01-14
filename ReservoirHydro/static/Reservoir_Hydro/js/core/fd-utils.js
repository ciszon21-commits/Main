/**
 * 排洪演算平台 - 工具函數模組
 */
class Utils {
    constructor() {
        this.toastContainer = null;
        this.toastCounter = 0;
        this.init();
    }

    /**
     * 初始化
     */
    init() {
        // 等待 DOM 載入
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.createToastContainer());
        } else {
            this.createToastContainer();
        }
    }

    /**
     * 創建吐司容器
     */
    createToastContainer() {
        // 移除現有容器
        const existing = document.querySelector('.toast-container');
        if (existing) {
            existing.remove();
        }

        // 創建新容器
        this.toastContainer = document.createElement('div');
        this.toastContainer.className = 'toast-container';
        document.body.appendChild(this.toastContainer);
        
        // console.log('吐司容器已創建');
    }

    /**
     * 顯示訊息 - 極簡版本
     */
    showMessage(type, message) {
        // console.log(`顯示訊息: [${type}] ${message}`);
        
        // 確保容器存在
        if (!this.toastContainer) {
            this.createToastContainer();
        }

        // 創建吐司 ID
        const toastId = `toast-${++this.toastCounter}`;
        
        // 設定圖標和樣式
        let icon;
        switch(type) {
            case 'success':
                icon = '✓';
                break;
            case 'error':
                icon = '✗';
                break;
            case 'warning':
                icon = '⚠';
                break;
            case 'info':
            default:
                icon = 'ℹ';
                break;
        }

        // 創建吐司元素
        const toast = document.createElement('div');
        toast.className = `custom-toast ${type}`;
        toast.id = toastId;
        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${message}</span>
            <button class="toast-close">&times;</button>
        `;

        // 添加到容器
        this.toastContainer.appendChild(toast);

        // 為關閉按鈕添加事件監聽器 (修正的部分)
        const closeButton = toast.querySelector('.toast-close');
        closeButton.addEventListener('click', () => {
            this.closeToast(toastId);
        });

        // 立即顯示 (使用 setTimeout 確保 DOM 更新)
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // 5秒後自動隱藏
        setTimeout(() => {
            this.closeToast(toastId);
        }, 5000);

        return toastId;
    }

    /**
     * 關閉特定吐司
     */
    closeToast(toastId) {
        const toast = document.getElementById(toastId);
        if (!toast) return;

        toast.classList.remove('show');
        toast.classList.add('hide');

        // 300ms 後移除元素
        setTimeout(() => {
            if (toast && toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    /**
     * 清除所有吐司
     */
    clearAllToasts() {
        if (this.toastContainer) {
            this.toastContainer.innerHTML = '';
        }
        // console.log('已清除所有吐司');
    }

    /**
     * 測試吐司
     */
    testToast() {
        this.showMessage('success', '這是成功訊息');
        setTimeout(() => this.showMessage('error', '這是錯誤訊息'), 1000);
        setTimeout(() => this.showMessage('warning', '這是警告訊息'), 2000);
        setTimeout(() => this.showMessage('info', '這是資訊訊息'), 3000);
    }

    /**
     * 獲取 CSRF Token
     */
    getCookie(name) {
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

    /**
     * 載入狀態管理
     */
    showLoading(step, action) {
        const actionConfigs = {
            'upload': { selector: `button[onclick="uploadData(${step})"]`, text: '<i class="bi bi-arrow-repeat spinner-border-sm"></i> 上傳中...' },
            'save': { selector: `button[onclick="saveData(${step})"]`, text: '<i class="bi bi-arrow-repeat spinner-border-sm"></i> 保存中...' },
            'draw': { selector: `button[onclick="drawChart(${step})"]`, text: '<i class="bi bi-arrow-repeat spinner-border-sm"></i> 繪圖中...' },
            'export': { selector: `button[onclick="exportChart(${step})"]`, text: '<i class="bi bi-arrow-repeat spinner-border-sm"></i> 匯出中...' },
            'adjust': { selector: `button[onclick="adjustTimeStep(${step})"]`, text: '<i class="bi bi-arrow-repeat spinner-border-sm"></i> 調整中...' },
            'save-adjusted': { selector: `button[onclick="saveAdjustedData(${step})"]`, text: '<i class="bi bi-arrow-repeat spinner-border-sm"></i> 匯出中...' }
        };

        const config = actionConfigs[action];
        if (config) {
            const button = document.querySelector(config.selector);
            if (button) {
                button.innerHTML = config.text;
                button.disabled = true;
            }
        }
    }

    hideLoading(step, action) {
        const actionConfigs = {
            'upload': { selector: `button[onclick="uploadData(${step})"]`, text:'<i class="bi bi-upload"></i> 數據輸入' },
            'save': { selector: `button[onclick="saveData(${step})"]`, text: '<i class="bi bi-download"></i> 數據存檔' },
            'draw': { selector: `button[onclick="drawChart(${step})"]`, text: step === 5 ? '<i class="bi bi-graph-up"></i> 排洪演算' : '<i class="bi bi-graph-up"></i> 數據繪圖' },
            'export': { selector: `button[onclick="exportChart(${step})"]`, text:'<i class="bi bi-save"></i> 出圖存檔' },
            'adjust': { selector: `button[onclick="adjustTimeStep(${step})"]`, text: '<i class="bi bi-clock-history"></i> 時距調整' },
            'save-adjusted': { selector: `button[onclick="saveAdjustedData(${step})"]`, text: '<i class="bi bi-download"></i> 數據存檔' }
        };

        const config = actionConfigs[action];
        if (config) {
            const button = document.querySelector(config.selector);
            if (button) {
                button.innerHTML = config.text;
                button.disabled = false;
            }
        }
    }

    /**
     * 文件大小驗證
     */
    validateFileSize(file, maxSizeMB = 100) {
        const maxSize = maxSizeMB * 1024 * 1024;
        if (file.size > maxSize) {
            this.showMessage('error', `檔案大小不能超過 ${maxSizeMB}MB`);
            return false;
        }
        return true;
    }

    /**
     * 文件類型驗證
     */
    validateFileType(file, allowedTypes = ['xlsx', 'xls', 'xlsm', 'csv']) {  // 默認包含 xlsm
        const fileExtension = file.name.split('.').pop().toLowerCase();
        if (!allowedTypes.includes(fileExtension)) {
            this.showMessage('error', `僅支援 ${allowedTypes.join(', ')} 格式的檔案`);
            return false;
        }
        return true;
    }

    /**
     * 數據格式化
     */
    formatNumber(value, decimals = 3) {
        return parseFloat(value).toFixed(decimals);
    }

    formatLargeNumber(value) {
        return parseFloat(value).toLocaleString();
    }

    /**
     * 下載檔案通用方法
     */
    downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
}

// 創建全局實例
window.fdUtils = new Utils();
// console.log('fdUtils 已初始化');