// Carbon Estimation Calculator JavaScript
// Real-time calculation for carbon emissions and costs

class CarbonCalculator {
    constructor() {
        this.quantityInputs = document.querySelectorAll('.quantity-input');
        // Maps to track state
        this.initialValues = new Map();
        this.unsavedCategories = new Set();
        this.init();
    }

    init() {
        // Track initial values
        this.quantityInputs.forEach(input => {
            const val = parseFloat(input.value) || 0;
            this.initialValues.set(input.id || this.generateId(input), val);
        });

        // Add beforeunload listener
        window.addEventListener('beforeunload', (e) => {
            if (this.unsavedCategories.size > 0) {
                e.preventDefault();
                e.returnValue = ''; // Standard for modern browsers
            }
        });
        // Add event listeners to all quantity inputs
        this.quantityInputs.forEach(input => {
            // Assign ID if missing for tracking
            if (!input.id) input.id = this.generateId(input);

            input.addEventListener('input', this.debounce(() => {
                this.calculateRow(input);
                this.updateCategoryTotals();
                this.updateGrandTotals();
                this.checkDirtyState(input);
            }, 100));

            // Initial calculation for rows with default values
            if (parseFloat(input.value) > 0) {
                this.calculateRow(input);
            }
        });

        // Add collapse/expand functionality
        this.initCollapseButtons();

        // Initial totals calculation
        this.updateCategoryTotals();
        this.updateGrandTotals();
    }

    initCollapseButtons() {
        // Make category titles clickable for collapse/expand
        const categoryHeaders = document.querySelectorAll('.category-header');

        categoryHeaders.forEach(header => {
            const categoryTitle = header.querySelector('.category-title');
            const categoryId = header.dataset.categoryId;

            categoryTitle.style.cursor = 'pointer';
            categoryTitle.style.userSelect = 'none';

            categoryTitle.addEventListener('click', () => {
                const categoryRows = document.querySelectorAll(`.data-row[data-category-id="${categoryId}"]`);

                // Toggle collapsed state
                const isCollapsed = header.classList.contains('collapsed');

                if (isCollapsed) {
                    // Expand
                    header.classList.remove('collapsed');
                    categoryRows.forEach(row => row.classList.remove('collapsed'));
                } else {
                    // Collapse
                    header.classList.add('collapsed');
                    categoryRows.forEach(row => row.classList.add('collapsed'));
                }
            });
        });

        // Add global collapse/expand button
        const globalBtn = document.getElementById('global-collapse-btn');
        if (globalBtn) {
            globalBtn.addEventListener('click', () => {
                const allExpanded = document.querySelectorAll('.category-header:not(.collapsed)').length === categoryHeaders.length;

                categoryHeaders.forEach(header => {
                    const categoryId = header.dataset.categoryId;
                    const categoryRows = document.querySelectorAll(`.data-row[data-category-id="${categoryId}"]`);

                    if (allExpanded) {
                        // Collapse all
                        header.classList.add('collapsed');
                        categoryRows.forEach(row => row.classList.add('collapsed'));
                    } else {
                        // Expand all
                        header.classList.remove('collapsed');
                        categoryRows.forEach(row => row.classList.remove('collapsed'));
                    }
                });

                // Update button text
                globalBtn.textContent = allExpanded ? '▲' : '▼';
            });
        }
    }

    calculateRow(input) {
        const row = input.closest('.data-row');
        if (!row) return;

        const quantity = parseFloat(input.value) || 0;
        const carbonBefore = parseFloat(row.dataset.carbonBefore) || 0;
        const carbonAfter = parseFloat(row.dataset.carbonAfter) || 0;

        // Calculate carbon totals
        const totalCarbonBefore = quantity * carbonBefore;  // 減碳前碳排總量
        const totalCarbonAfter = quantity * carbonAfter;    // 減碳後碳排總量

        // Update display (only 2 calculated columns now: carbon before and after)
        const cells = row.querySelectorAll('.calculated');
        if (cells[0]) cells[0].textContent = this.formatNumber(totalCarbonBefore);
        if (cells[1]) cells[1].textContent = this.formatNumber(totalCarbonAfter);

        // Add animation effect
        this.animateValue(cells);
    }

    updateCategoryTotals() {
        // Get all categories
        const categoryHeaders = document.querySelectorAll('.category-header');

        categoryHeaders.forEach(header => {
            // Get categoryId directly from header element
            const categoryId = header.dataset.categoryId;

            // Find all rows in this category
            const categoryRows = document.querySelectorAll(`.data-row[data-category-id="${categoryId}"]`);

            let totalCarbonBefore = 0;
            let totalCarbonAfter = 0;

            categoryRows.forEach(row => {
                // Skip rows without quantity input (level 2 items)
                const quantityInput = row.querySelector('.quantity-input');
                if (!quantityInput) return;

                const quantity = parseFloat(quantityInput.value) || 0;
                const carbonBefore = parseFloat(row.dataset.carbonBefore) || 0;
                const carbonAfter = parseFloat(row.dataset.carbonAfter) || 0;

                totalCarbonBefore += quantity * carbonBefore;
                totalCarbonAfter += quantity * carbonAfter;
            });

            // Update category subtotals (only carbon, not cost)
            const subtotals = header.querySelectorAll('.category-subtotal');
            subtotals.forEach(cell => {
                const type = cell.dataset.type;

                switch (type) {
                    case 'carbon-before':
                        cell.textContent = this.formatNumber(totalCarbonBefore);
                        break;
                    case 'carbon-after':
                        cell.textContent = this.formatNumber(totalCarbonAfter);
                        break;
                }
            });
        });
    }

    updateGrandTotals() {
        let grandCarbonBefore = 0;
        let grandCarbonAfter = 0;

        // Sum all data rows (skip level 2 items without quantity inputs)
        document.querySelectorAll('.data-row').forEach(row => {
            const quantityInput = row.querySelector('.quantity-input');
            if (!quantityInput) return;

            const quantity = parseFloat(quantityInput.value) || 0;
            const carbonBefore = parseFloat(row.dataset.carbonBefore) || 0;
            const carbonAfter = parseFloat(row.dataset.carbonAfter) || 0;

            grandCarbonBefore += quantity * carbonBefore;
            grandCarbonAfter += quantity * carbonAfter;
        });

        // Update summary cards (top of page)
        this.updateSummaryCard('total-carbon-before', grandCarbonBefore);
        this.updateSummaryCard('total-carbon-after', grandCarbonAfter);

        // Update footer totals
        this.updateSummaryCard('grand-total-carbon-before', grandCarbonBefore);
        this.updateSummaryCard('grand-total-carbon-after', grandCarbonAfter);
    }

    updateSummaryCard(elementId, value, decimals) {
        const element = document.getElementById(elementId);
        if (element) {
            const formatted = this.formatNumber(value, decimals);
            if (element.textContent !== formatted) {
                element.textContent = formatted;
                element.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    element.style.transform = 'scale(1)';
                }, 200);
            }
        }
    }

    formatNumber(num, decimals = 2) {
        if (isNaN(num) || num === 0) {
            return decimals > 0 ? '0.' + '0'.repeat(decimals) : '0';
        }

        // Format with thousand separators and specified decimals
        return num.toLocaleString('zh-TW', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    animateValue(cells) {
        cells.forEach(cell => {
            cell.style.transition = 'background-color 0.3s ease';
            cell.style.backgroundColor = 'rgba(20, 184, 166, 0.15)';
            setTimeout(() => {
                cell.style.backgroundColor = 'rgba(20, 184, 166, 0.05)';
            }, 300);
        });
    }

    debounce(func, wait) {
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

    generateId(input) {
        // Generate a unique ID based on item ID if input id is missing
        const row = input.closest('.data-row');
        return `qty-${row.dataset.itemId}`;
    }

    checkDirtyState(input) {
        const currentVal = parseFloat(input.value) || 0;
        const initialVal = this.initialValues.get(input.id) || 0;
        const row = input.closest('.data-row');
        const categoryId = row.dataset.categoryId;
        const categoryHeader = document.querySelector(`.category-header[data-category-id="${categoryId}"]`);
        const saveBtn = categoryHeader.querySelector('.category-save-btn');

        if (currentVal !== initialVal) {
            input.classList.add('unsaved');
            saveBtn.classList.add('unsaved');
            saveBtn.textContent = '未儲存';
            this.unsavedCategories.add(categoryId);

            // Show Save All button
            const saveAllBtn = document.getElementById('save-all-btn');
            if (saveAllBtn) saveAllBtn.style.display = 'block';

        } else {
            input.classList.remove('unsaved');
            // Check if any other inputs in this category are unsaved
            const categoryRows = document.querySelectorAll(`.data-row[data-category-id="${categoryId}"]`);
            let hasUnsaved = false;
            categoryRows.forEach(r => {
                const qtyInput = r.querySelector('.quantity-input');
                if (qtyInput && qtyInput.classList.contains('unsaved')) {
                    hasUnsaved = true;
                }
            });

            if (!hasUnsaved) {
                saveBtn.classList.remove('unsaved');
                saveBtn.textContent = '儲存';
                this.unsavedCategories.delete(categoryId);
            }

            // Checks if there are any remaining unsaved categories globally
            if (this.unsavedCategories.size === 0) {
                const saveAllBtn = document.getElementById('save-all-btn');
                // Optional: hide it if clean? User wanted button "added", not "toggle".
                // But earlier I decided to toggle. Let's keep it visible but maybe opacity?
                // Or just keep it displayed if user prefers. 
                // Decision: Keep it displayed always once it appears, or toggle. 
                // Let's toggle to be consistent with "There are changes". 
                if (saveAllBtn) saveAllBtn.style.display = 'none';
            }
        }
    }

    resetDirtyState(categoryId) {
        // Reset initial values to current values for all inputs in this category
        const categoryRows = document.querySelectorAll(`.data-row[data-category-id="${categoryId}"]`);
        const saveBtn = document.querySelector(`.category-header[data-category-id="${categoryId}"] .category-save-btn`);

        categoryRows.forEach(row => {
            const input = row.querySelector('.quantity-input');
            if (input) {
                const currentVal = parseFloat(input.value) || 0;
                this.initialValues.set(input.id, currentVal);
                input.classList.remove('unsaved');
            }
        });

        if (saveBtn) {
            saveBtn.classList.remove('unsaved');
            saveBtn.textContent = '儲存';
        }

        this.unsavedCategories.delete(categoryId);
    }

    resetAllDirtyStates() {
        const categoryHeaders = document.querySelectorAll('.category-header');
        categoryHeaders.forEach(header => {
            const categoryId = header.dataset.categoryId;
            this.resetDirtyState(categoryId);
        });

        // Hide Save All button
        const saveAllBtn = document.getElementById('save-all-btn');
        if (saveAllBtn) saveAllBtn.style.display = 'none';

        this.unsavedCategories.clear();
    }
}

// Initialize calculator when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.carbonCalculator = new CarbonCalculator();
    console.log('Carbon Estimation Calculator initialized');

    // Back to Top Button Logic
    const backToTopBtn = document.getElementById('back-to-top');
    if (backToTopBtn) {
        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });

        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        });
    }
});
