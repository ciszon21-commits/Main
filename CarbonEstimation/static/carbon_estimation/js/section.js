// ============================================================================
// 斷面計算器 JavaScript - 即時計算碳排總量 + 未儲存變更追蹤
// ============================================================================

class SectionCalculator {
    constructor() {
        this.quantityInputs = document.querySelectorAll('.quantity-input');
        this.initialValues = new Map();
        this.unsavedCategories = new Set();
        this.init();
    }

    init() {
        // 追蹤初始值
        this.quantityInputs.forEach(input => {
            const val = parseFloat(input.value) || 0;
            const id = input.dataset.itemId || this.generateId(input);
            this.initialValues.set(id, val);
        });

        // beforeunload 監聽
        window.addEventListener('beforeunload', (e) => {
            if (this.unsavedCategories.size > 0) {
                e.preventDefault();
                e.returnValue = '';
            }
        });

        // 監聽數量輸入
        this.quantityInputs.forEach(input => {
            input.addEventListener('input', () => {
                this.calculateRow(input);
                this.updateCategorySubtotals();
                this.updateGrandTotals();
                this.checkDirtyState(input);
            });
        });

        // 全部收合/展開功能
        this.initCollapseButtons();

        // 回到頂部按鈕
        this.initBackToTop();

        // 載入方案數據
        const urlParams = new URLSearchParams(window.location.search);
        const scenarioId = urlParams.get('scenario');
        if (scenarioId) {
            this.loadScenarioData(scenarioId);
        }

        // 初始計算
        this.updateCategorySubtotals();
        this.updateGrandTotals();
    }

    initCollapseButtons() {
        const globalCollapseBtn = document.getElementById('global-collapse-btn');
        let isCollapsed = false;

        if (globalCollapseBtn) {
            globalCollapseBtn.addEventListener('click', () => {
                const categoryHeaders = document.querySelectorAll('.category-header');
                isCollapsed = !isCollapsed;

                categoryHeaders.forEach(header => {
                    const categoryId = header.dataset.categoryId;
                    const rows = document.querySelectorAll(`tr.data-row[data-category-id="${categoryId}"]`);
                    rows.forEach(row => {
                        row.style.display = isCollapsed ? 'none' : '';
                    });
                });
                // 統一為上下箭頭：▲收合/▼展開
                globalCollapseBtn.textContent = isCollapsed ? '▲' : '▼';
            });
        }

        // 點擊分類標題收合/展開
        document.querySelectorAll('.category-header').forEach(header => {
            const titleCell = header.querySelector('.category-title');
            if (titleCell) {
                titleCell.style.cursor = 'pointer';
                titleCell.addEventListener('click', (e) => {
                    if (e.target.classList.contains('category-save-btn')) return;

                    const categoryId = header.dataset.categoryId;
                    const rows = document.querySelectorAll(`tr.data-row[data-category-id="${categoryId}"]`);
                    const isHidden = rows[0]?.style.display === 'none';

                    rows.forEach(row => {
                        row.style.display = isHidden ? '' : 'none';
                    });
                });
            }
        });
    }

    initBackToTop() {
        const backToTopBtn = document.getElementById('back-to-top');
        if (!backToTopBtn) return;

        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        });

        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    calculateRow(input) {
        const row = input.closest('tr');
        if (!row) return;

        const quantity = parseFloat(input.value) || 0;
        const carbonPerUnit = parseFloat(row.dataset.carbon) || 0;
        const carbonTotal = quantity * carbonPerUnit;

        // 更新該行的碳排總量
        const carbonCell = row.querySelector('.result-carbon');
        if (carbonCell) {
            carbonCell.textContent = this.formatNumber(carbonTotal);

            // 移除動畫效果，改為即時灰色高亮
            carbonCell.style.transition = 'none';
            carbonCell.style.backgroundColor = '#e5e7eb';
            setTimeout(() => {
                carbonCell.style.backgroundColor = '#f9fafb';
            }, 300);
        }
    }

    updateCategorySubtotals() {
        const categoryIds = [...new Set(
            Array.from(document.querySelectorAll('tr.data-row'))
                .map(row => row.dataset.categoryId)
        )];

        categoryIds.forEach(categoryId => {
            const rows = document.querySelectorAll(`tr.data-row[data-category-id="${categoryId}"]`);
            let categoryCarbon = 0;

            rows.forEach(row => {
                const input = row.querySelector('.quantity-input');
                if (!input) return;

                const quantity = parseFloat(input.value) || 0;
                const carbonPerUnit = parseFloat(row.dataset.carbon) || 0;
                categoryCarbon += quantity * carbonPerUnit;
            });

            // 更新分類小計
            const subtotalCell = document.querySelector(
                `.category-subtotal[data-category-id="${categoryId}"][data-type="carbon"]`
            );
            if (subtotalCell) {
                subtotalCell.textContent = this.formatNumber(categoryCarbon);
            }
        });
    }

    updateGrandTotals() {
        let grandCarbon = 0;

        document.querySelectorAll('tr.data-row').forEach(row => {
            const input = row.querySelector('.quantity-input');
            if (!input) return;

            const quantity = parseFloat(input.value) || 0;
            const carbonPerUnit = parseFloat(row.dataset.carbon) || 0;
            grandCarbon += quantity * carbonPerUnit;
        });

        // 更新表格底部總計
        const grandTotalEl = document.getElementById('grand-total-carbon');
        if (grandTotalEl) {
            grandTotalEl.textContent = this.formatNumber(grandCarbon);
        }

        // 更新頂部彙總卡片
        const totalCarbonEl = document.getElementById('total-carbon');
        if (totalCarbonEl) {
            totalCarbonEl.textContent = this.formatNumber(grandCarbon);
        }
    }

    formatNumber(num) {
        if (num === 0) return '0.00';
        return new Intl.NumberFormat('zh-TW', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num);
    }

    checkDirtyState(input) {
        const itemId = input.dataset.itemId;
        const currentVal = parseFloat(input.value) || 0;
        const initialVal = this.initialValues.get(itemId) || 0;

        const row = input.closest('tr.data-row');  // 修正：明確指定 tr.data-row
        const categoryId = row?.dataset.categoryId;

        console.log('Check dirty state:', { itemId, currentVal, initialVal, categoryId });

        if (!categoryId) {
            console.warn('No categoryId found for input:', input);
            return;
        }

        const categoryHeader = document.querySelector(`.category-header[data-category-id="${categoryId}"]`);
        const saveBtn = categoryHeader?.querySelector('.category-save-btn');

        console.log('Category header and save button:', { categoryHeader, saveBtn });

        if (currentVal !== initialVal) {
            input.classList.add('unsaved');
            if (saveBtn) {
                saveBtn.classList.add('unsaved');
                saveBtn.textContent = '未儲存';
                console.log('✅ Set unsaved state for category:', categoryId);
            } else {
                console.warn('⚠️ Save button not found');
            }
            this.unsavedCategories.add(categoryId);

            // 啟用全部儲存按鈕
            const saveAllBtn = document.getElementById('save-all-btn');
            if (saveAllBtn) saveAllBtn.disabled = false;

        } else {
            input.classList.remove('unsaved');

            // 檢查該分類下是否還有其他未儲存的項目
            const categoryRows = document.querySelectorAll(`tr.data-row[data-category-id="${categoryId}"]`);
            let hasUnsaved = false;
            categoryRows.forEach(r => {
                const qtyInput = r.querySelector('.quantity-input');
                if (qtyInput?.classList.contains('unsaved')) {
                    hasUnsaved = true;
                }
            });

            if (!hasUnsaved) {
                if (saveBtn) {
                    saveBtn.classList.remove('unsaved');
                    saveBtn.textContent = '儲存';
                }
                this.unsavedCategories.delete(categoryId);
            }

            // 如果沒有任何未儲存的分類，停用全部儲存按鈕
            if (this.unsavedCategories.size === 0) {
                const saveAllBtn = document.getElementById('save-all-btn');
                if (saveAllBtn) saveAllBtn.disabled = true;
            }
        }
    }

    resetDirtyState(categoryId) {
        const categoryRows = document.querySelectorAll(`tr.data-row[data-category-id="${categoryId}"]`);
        const saveBtn = document.querySelector(`.category-header[data-category-id="${categoryId}"] .category-save-btn`);

        categoryRows.forEach(row => {
            const input = row.querySelector('.quantity-input');
            if (input) {
                const itemId = input.dataset.itemId;
                const currentVal = parseFloat(input.value) || 0;
                this.initialValues.set(itemId, currentVal);
                input.classList.remove('unsaved');
            }
        });

        if (saveBtn) {
            saveBtn.classList.remove('unsaved');
            saveBtn.textContent = '儲存';
        }

        this.unsavedCategories.delete(categoryId);
        console.log('✅ Reset dirty state for category:', categoryId);
    }

    resetAllDirtyStates() {
        const categoryHeaders = document.querySelectorAll('.category-header');
        categoryHeaders.forEach(header => {
            const categoryId = header.dataset.categoryId;
            this.resetDirtyState(categoryId);
        });

        const saveAllBtn = document.getElementById('save-all-btn');
        if (saveAllBtn) saveAllBtn.disabled = true;

        this.unsavedCategories.clear();
    }

    async loadScenarioData(scenarioId) {
        try {
            const response = await fetch(`/carbon/api/scenarios/${scenarioId}/load-section/`);
            const result = await response.json();

            if (result.success) {
                // 填充數量
                Object.entries(result.data).forEach(([itemId, quantity]) => {
                    const input = document.querySelector(`.quantity-input[data-item-id="${itemId}"]`);
                    if (input) {
                        input.value = quantity;
                        // 更新初始值
                        this.initialValues.set(itemId, parseFloat(quantity) || 0);
                        this.calculateRow(input);
                    }
                });

                this.updateCategorySubtotals();
                this.updateGrandTotals();

                // 更新副標題顯示方案資訊
                this.updatePageSubtitle(result.scenario);

                console.log('✅ 方案數據已載入:', result.scenario.scenario_name);
            }
        } catch (error) {
            console.error('❌ 載入方案數據失敗:', error);
        }
    }

    updatePageSubtitle(scenarioInfo) {
        // Keep the original page title, show scenario info in subtitle
        const subtitleEl = document.querySelector('.subtitle');
        if (subtitleEl) {
            subtitleEl.textContent = `${scenarioInfo.project_name} - ${scenarioInfo.scenario_name}`;
        }
    }

    generateId(input) {
        const row = input.closest('.data-row');
        return row?.dataset.itemId || `item-${Math.random()}`;
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    window.sectionCalculator = new SectionCalculator();
    console.log('Section Calculator initialized with unsaved changes tracking');
});
