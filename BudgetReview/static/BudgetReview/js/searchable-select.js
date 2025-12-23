/**
 * BudgetReview - 可搜尋下拉選單組件
 * searchable-select.js
 * 為 select 元素添加搜尋功能（單選或多選）
 */

document.addEventListener('DOMContentLoaded', function () {
    // 查找所有帶有 searchable-select 類名的 select 元素
    const searchableSelects = document.querySelectorAll('.searchable-select');

    searchableSelects.forEach(select => {
        initializeSearchableSelect(select);
    });
});

/**
 * 初始化可搜尋下拉選單
 * @param {HTMLSelectElement} select - 原始的 select 元素
 */
function initializeSearchableSelect(select) {
    const isMultiple = select.hasAttribute('multiple');
    
    // 建立容器元素
    const container = document.createElement('div');
    container.className = 'searchable-select-container';

    // 建立搜尋輸入框
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'search-input';
    searchInput.placeholder = isMultiple ? '輸入姓名搜尋並點擊加入...' : '輸入姓名搜尋...';

    // 建立選項列表
    const optionsList = document.createElement('div');
    optionsList.className = 'options-list';

    // 建立多選 chips 容器
    const chipsContainer = document.createElement('div');
    chipsContainer.className = 'select-multiple-chips';

    // 儲存原始選項
    const originalOptions = Array.from(select.options);

    // 隱藏原始 select
    select.style.display = 'none';
    
// 插入新建立的元素
    select.parentNode.insertBefore(container, select);
    container.appendChild(searchInput);
    container.appendChild(optionsList);
    if (isMultiple) {
        container.appendChild(chipsContainer);
    }

    /**
     * 渲染選項列表
     * @param {string} filter - 搜尋過濾字串
     */
    function renderOptions(filter = '') {
        optionsList.innerHTML = '';
        let hasResults = false;

        originalOptions.forEach(opt => {
            // 跳過空選項（僅對單選）
            if (opt.value === '' && !isMultiple) return;

            // 過濾選項
            if (opt.text.toLowerCase().includes(filter.toLowerCase())) {
                const item = document.createElement('div');
                item.className = 'option-item';
                if (opt.selected) item.classList.add('selected');
                item.textContent = opt.text;
                item.dataset.value = opt.value;

                // 點擊事件
                item.addEventListener('click', (e) => {
                    e.stopPropagation();
                    
                    if (isMultiple) {
                        // 多選模式：切換選中狀態
                        opt.selected = !opt.selected;
                        renderOptions(searchInput.value);
                    } else {
                        // 單選模式：選中當前項，取消其他項
                        originalOptions.forEach(o => o.selected = false);
                        opt.selected = true;
                        searchInput.value = opt.text;
                        optionsList.style.display = 'none';
                    }
                    
                    updateUI();
                });

                optionsList.appendChild(item);
                hasResults = true;
            }
        });

        // 顯示/隱藏選項列表
        optionsList.style.display = (hasResults && (filter !== '' || !isMultiple)) ? 'block' : 'none';
    }

    /**
     * 更新 UI 顯示
     */
    function updateUI() {
        if (isMultiple) {
            // 多選模式：更新 chips 顯示
            chipsContainer.innerHTML = '';
            
            originalOptions.forEach(opt => {
                if (opt.selected) {
                    const chip = document.createElement('div');
                    chip.className = 'chip';
                    chip.innerHTML = `${opt.text} <span class="chip-remove" data-value="${opt.value}">×</span>`;
                    
                    // 移除 chip 的點擊事件
                    chip.querySelector('.chip-remove').onclick = (e) => {
                        e.stopPropagation();
                        opt.selected = false;
                        updateUI();
                    };
                    
                    chipsContainer.appendChild(chip);
                }
            });
        } else {
            // 單選模式：更新輸入框顯示
            const selected = originalOptions.find(o => o.selected);
            if (selected && selected.value !== '') {
                searchInput.value = selected.text;
            }
        }
        
        // 觸發 change 事件（重要：讓 Django 表單知道值已改變）
        select.dispatchEvent(new Event('change'));
    }

    // 搜尋輸入事件
    searchInput.addEventListener('input', (e) => {
        renderOptions(e.target.value);
    });

    // 聚焦時顯示選項
    searchInput.addEventListener('focus', () => {
        renderOptions(searchInput.value);
    });

    // 點擊外部關閉選項列表
    document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
            optionsList.style.display = 'none';
        }
    });

    // 初始化 UI
    updateUI();
}
