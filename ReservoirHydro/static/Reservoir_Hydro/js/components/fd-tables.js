/**
 * 排洪演算平台 - 表格管理模組
 */
class TableManager {
    constructor() {
        this.utils = window.fdUtils;
        this.currentSort = { column: null, direction: null };
    }

    /**
     * 更新步驟1表格 (HAV)
     */
    updateStep1Table(data) {
        const tableBody = document.getElementById('reservoir-data-table');
        if (!tableBody) {
            console.error('找不到 reservoir-data-table 元素');
            return;
        }

        const processedData = data.map((row, index) => ({
            originalIndex: index + 1,
            level: parseFloat(row.level || 0),
            area: parseFloat(row.area || 0),
            volume: parseFloat(row.volume || 0)
        }));

        this.renderTable(tableBody, processedData, this.getStep1RowRenderer());
        return processedData;
    }

    /**
     * 更新步驟2原始數據表格
     */
    updateStep2OriginalTable(data) {
        const tableBody = document.getElementById('inflow-original-table');
        if (!tableBody) {
            console.error('找不到 inflow-original-table 元素');
            return;
        }

        this.renderTable(tableBody, data, this.getStep2RowRenderer());
    }

    /**
     * 更新步驟2調整後數據表格
     */
    updateStep2AdjustedTable(data) {
        const tableBody = document.getElementById('inflow-adjusted-table');
        if (!tableBody) {
            console.error('找不到 inflow-adjusted-table 元素');
            return;
        }

        this.renderTable(tableBody, data, this.getStep2RowRenderer());
    }

    /**
     * 通用表格渲染方法
     */
    renderTable(tableBody, data, rowRenderer) {
        tableBody.innerHTML = '';

        if (!data || data.length === 0) {
            const tr = document.createElement('tr');
            tr.innerHTML = '<td colspan="3" class="text-center text-muted">尚無數據</td>';
            tableBody.appendChild(tr);
            return;
        }

        data.forEach((row, index) => {
            const tr = document.createElement('tr');
            tr.className = 'new-data';
            tr.innerHTML = rowRenderer(row, index);

            // 添加懸停效果
            this.addRowHoverEffect(tr);

            // 添加動畫效果
            tr.style.opacity = '0';
            tr.style.transform = 'translateY(20px)';
            tableBody.appendChild(tr);

            setTimeout(() => {
                tr.style.transition = 'all 0.3s ease';
                tr.style.opacity = '1';
                tr.style.transform = 'translateY(0)';
            }, index * 30);
        });

        // 移除高亮效果
        setTimeout(() => {
            document.querySelectorAll(`#${tableBody.id} tr.new-data`).forEach(tr => {
                tr.classList.remove('new-data');
            });
        }, 2000);
    }

    /**
     * 步驟1行渲染器
     */
    getStep1RowRenderer() {
        return (row, index) => `
            <td style="color:rgb(81, 75, 162); font-weight: 500;">${this.utils.formatNumber(row.level, 0)}</td>
            <td style="color:rgb(75, 127, 162); font-weight: 500;">${this.utils.formatNumber(row.area, 3)}</td>
            <td style="color: rgb(81, 75, 162); font-weight: 500;">${this.utils.formatNumber(row.volume, 3)}</td>
        `;
    }

    /**
     * 步驟2行渲染器
     */
    getStep2RowRenderer() {
        return (row, index) => `
            <td style="color:rgb(81, 75, 162); font-weight: 500;">${this.utils.formatNumber(row.Time, 2)}</td>
            <td style="color:rgb(75, 127, 162); font-weight: 500;">${this.utils.formatNumber(row.Flow, 3)}</td>
        `;
    }

    /**
     * 添加行懸停效果
     */
    addRowHoverEffect(tr) {
        tr.addEventListener('mouseenter', function () {
            this.style.backgroundColor = 'rgba(13, 110, 253, 0.075)';
            this.style.transform = 'scale(1.01)';
            this.style.transition = 'all 0.2s ease';
        });

        tr.addEventListener('mouseleave', function () {
            this.style.backgroundColor = '';
            this.style.transform = '';
        });
    }

    /**
     * 表格排序功能
     */
    sortTable(column, direction, currentData) {
        if (!currentData || currentData.length === 0) {
            this.utils.showMessage('error', '沒有數據可以排序');
            return currentData;
        }

        // 更新排序按鈕狀態
        document.querySelectorAll('.sort-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        const activeBtn = document.querySelector(`[onclick="sortTable('${column}', '${direction}')"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }

        const sortedData = [...currentData].sort((a, b) => {
            let valueA, valueB;

            switch (column) {
                case 'index':
                    valueA = a.originalIndex;
                    valueB = b.originalIndex;
                    break;
                case 'level':
                    valueA = a.level;
                    valueB = b.level;
                    break;
                case 'area':
                    valueA = a.area;
                    valueB = b.area;
                    break;
                case 'volume':
                    valueA = a.volume;
                    valueB = b.volume;
                    break;
                default:
                    return 0;
            }

            return direction === 'asc' ? valueA - valueB : valueB - valueA;
        });

        this.currentSort = { column, direction };

        // 重新渲染表格
        const tableBody = document.getElementById('reservoir-data-table');
        this.renderTable(tableBody, sortedData, this.getStep1RowRenderer());

        const columnNames = {
            'index': '索引',
            'level': '水位',
            'area': '面積',
            'volume': '容量'
        };
        const directionText = direction === 'asc' ? '由小到大' : '由大到小';

        this.utils.showMessage('success', `已按 ${columnNames[column]} ${directionText} 排序`);

        return sortedData;
    }

    /**
     * 步驟2入流數據排序
     */
    sortInflowTable(column, direction, tableType) {
        let currentData, tableId, renderFunction;

        if (tableType === 'original') {
            currentData = window.fdStep2.inflowOriginalData;
            tableId = 'inflow-original-table';
        } else if (tableType === 'adjusted') {
            currentData = window.fdStep2.inflowAdjustedData;
            tableId = 'inflow-adjusted-table';
        } else {
            this.utils.showMessage('error', '無效的表格類型');
            return null;
        }

        if (!currentData || currentData.length === 0) {
            this.utils.showMessage('error', '沒有數據可以排序');
            return null;
        }

        // 更新排序按鈕狀態
        this.updateSortButtonStates(column, direction, tableType);

        // 執行排序
        const sortedData = [...currentData].sort((a, b) => {
            let valueA, valueB;

            switch (column) {
                case 'time':
                    valueA = parseFloat(a.Time);
                    valueB = parseFloat(b.Time);
                    break;
                case 'flow':
                    valueA = parseFloat(a.Flow);
                    valueB = parseFloat(b.Flow);
                    break;
                default:
                    return 0;
            }

            return direction === 'asc' ? valueA - valueB : valueB - valueA;
        });

        // 重新渲染表格
        const tableBody = document.getElementById(tableId);
        this.renderTable(tableBody, sortedData, this.getStep2RowRenderer());

        // 更新對應的數據
        if (tableType === 'original') {
            window.fdStep2.inflowOriginalData = sortedData;
        } else {
            window.fdStep2.inflowAdjustedData = sortedData;
        }

        const columnNames = {
            'time': '歷時',
            'flow': '流量'
        };
        const directionText = direction === 'asc' ? '由小到大' : '由大到小';

        this.utils.showMessage('success', `${tableType === 'original' ? '原始' : '調整後'}數據已按 ${columnNames[column]} ${directionText} 排序`);

        return sortedData;
    }

    /**
     * 更新排序按鈕狀態
     */
    updateSortButtonStates(column, direction, tableType) {
        // 清除所有相關的排序按鈕狀態
        const prefix = tableType === 'original' ? 'original' : 'adjusted';
        document.querySelectorAll(`[onclick*="'${prefix}'"]`).forEach(btn => {
            btn.classList.remove('active');
        });

        // 激活當前點擊的按鈕
        const activeBtn = document.querySelector(`[onclick="sortInflowTable('${column}', '${direction}', '${tableType}')"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }

    /**
     * 通用的步驟2表格排序方法（統一入口）
     */
    sortStep2Table(column, direction, tableType) {
        return this.sortInflowTable(column, direction, tableType);
    }
}

// 創建全局實例
window.fdTables = new TableManager();