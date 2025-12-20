/**
 * BudgetReview - Modal JavaScript
 * modal.js
 */

class Modal {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        this.backdrop = this.modal?.querySelector('.modal-backdrop');
        this.closeBtn = this.modal?.querySelector('.modal-close');
        this.modalBody = this.modal?.querySelector('.modal-body');

        this.init();
    }

    init() {
        if (!this.modal) return;

        // 關閉按鈕事件
        this.closeBtn?.addEventListener('click', () => this.close());

        // 點擊背景關閉 - 已禁用，只能通過按鈕關閉
        // this.backdrop?.addEventListener('click', (e) => {
        //     if (e.target === this.backdrop) {
        //         this.close();
        //     }
        // });

        // ESC 鍵關閉 - 已禁用，只能通過按鈕關閉
        // document.addEventListener('keydown', (e) => {
        //     if (e.key === 'Escape' && this.isOpen()) {
        //         this.close();
        //     }
        // });
    }

    open() {
        if (this.backdrop) {
            this.backdrop.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    close() {
        if (this.backdrop) {
            this.backdrop.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    isOpen() {
        return this.backdrop?.classList.contains('active');
    }

    setContent(html) {
        if (this.modalBody) {
            this.modalBody.innerHTML = html;
        }
    }

    showLoading() {
        this.setContent(`
            <div class="modal-loading">
                <div class="spinner"></div>
            </div>
        `);
    }
}

// 全域 Modal 實例
let editModal = null;
let createModal = null;
let disciplineModal = null;
let uploadModal = null;

document.addEventListener('DOMContentLoaded', function () {
    editModal = new Modal('editProjectModal');
    createModal = new Modal('createProjectModal');
    disciplineModal = new Modal('createDisciplineModal');
    uploadModal = new Modal('uploadFileModal');

    // 編輯按鈕點擊事件
    document.querySelectorAll('.btn-edit-modal').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const projectId = this.dataset.projectId;
            loadEditForm(projectId);
        });
    });
});

/**
 * 關閉當前開啟的 Modal
 */
function closeCurrentModal() {
    if (disciplineModal && disciplineModal.isOpen()) {
        disciplineModal.close();
    } else if (createModal && createModal.isOpen()) {
        createModal.close();
    } else if (editModal && editModal.isOpen()) {
        editModal.close();
    } else if (uploadModal && uploadModal.isOpen()) {
        uploadModal.close();
    }
}

/**
 * 載入編輯表單
 */
function loadEditForm(projectId) {
    if (!editModal) return;

    editModal.open();
    editModal.showLoading();

    fetch(`/budget/project/${projectId}/edit-ajax/`)
        .then(response => response.json())
        .then(data => {
            // 從 JSON 中提取 html 屬性
            if (data.html) {
                editModal.setContent(data.html);

                // 初始化表單提交
                const form = document.querySelector('#editProjectModal form');
                if (form) {
                    initFormSubmit(form, projectId);
                }

                // 初始化可搜尋下拉選單
                const searchableSelects = document.querySelectorAll('#editProjectModal .searchable-select');
                searchableSelects.forEach(select => {
                    if (typeof initializeSearchableSelect === 'function') {
                        initializeSearchableSelect(select);
                    }
                });
            } else {
                editModal.setContent('<p class="error-text">載入表單失敗：無效的回應格式</p>');
            }
        })
        .catch(error => {
            console.error('Error loading form:', error);
            editModal.setContent('<p class="error-text">載入表單失敗，請重試。</p>');
        });
}

/**
 * 開啟建立標案 Modal
 */
function openCreateModal() {
    if (!createModal) return;

    createModal.open();
    createModal.showLoading();

    fetch('/budget/project/create-ajax/')
        .then(response => response.json())
        .then(data => {
            if (data.html) {
                createModal.setContent(data.html);

                // 初始化表單提交
                const form = document.querySelector('#createProjectModal form');
                if (form) {
                    initCreateFormSubmit(form);
                }

                // 初始化可搜尋下拉選單
                const searchableSelects = document.querySelectorAll('#createProjectModal .searchable-select');
                searchableSelects.forEach(select => {
                    if (typeof initializeSearchableSelect === 'function') {
                        initializeSearchableSelect(select);
                    }
                });
            } else {
                createModal.setContent('<p class="error-text">載入表單失敗：無效的回應格式</p>');
            }
        })
        .catch(error => {
            console.error('Error loading form:', error);
            createModal.setContent('<p class="error-text">載入表單失敗，請重試。</p>');
        });
}

/**
 * 開啟建立專業分組 Modal
 */
function openDisciplineModal(projectId) {
    console.log('openDisciplineModal 被調用，projectId:', projectId);
    console.log('disciplineModal 對象:', disciplineModal);

    if (!disciplineModal) {
        console.error('disciplineModal 不存在！');
        return;
    }

    disciplineModal.open();
    disciplineModal.showLoading();

    fetch(`/budget/project/${projectId}/discipline/create-ajax/`)
        .then(response => response.json())
        .then(data => {
            if (data.html) {
                disciplineModal.setContent(data.html);

                // 初始化表單提交
                const form = document.querySelector('#createDisciplineModal form');
                if (form) {
                    initDisciplineFormSubmit(form, projectId);
                }

                // 初始化可搜尋下拉選單
                const searchableSelects = document.querySelectorAll('#createDisciplineModal .searchable-select');
                searchableSelects.forEach(select => {
                    if (typeof initializeSearchableSelect === 'function') {
                        initializeSearchableSelect(select);
                    }
                });
            } else {
                disciplineModal.setContent('<p class="error-text">載入表單失敗：無效的回應格式</p>');
            }
        })
        .catch(error => {
            console.error('Error loading form:', error);
            disciplineModal.setContent('<p class="error-text">載入表單失敗，請重試。</p>');
        });
}

/**
 * 初始化表單提交
 */
function initFormSubmit(form, projectId) {
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(form);

        fetch(`/budget/project/${projectId}/edit-ajax/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 關閉 Modal
                    editModal.close();

                    // 顯示成功訊息（可選）
                    showMessage('success', data.message || '標案已更新');

                    // 重新載入頁面或更新列表項目
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                } else {
                    // 顯示錯誤
                    if (data.html) {
                        editModal.setContent(data.html);
                        // 重新初始化表單
                        const newForm = document.querySelector('#editProjectModal form');
                        if (newForm) {
                            initFormSubmit(newForm, projectId);
                        }
                    } else {
                        showMessage('error', data.message || '更新失敗');
                    }
                }
            })
            .catch(error => {
                console.error('Error submitting form:', error);
                showMessage('error', '提交失敗，請重試');
            });
    });
}

/**
 * 初始化建立表單提交
 */
function initCreateFormSubmit(form) {
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(form);

        fetch('/budget/project/create-ajax/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 關閉 Modal
                    createModal.close();

                    // 顯示成功訊息
                    showMessage('success', data.message || '標案已建立');

                    // 重新載入頁面
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                } else {
                    // 顯示錯誤
                    if (data.html) {
                        createModal.setContent(data.html);
                        // 重新初始化表單
                        const newForm = document.querySelector('#createProjectModal form');
                        if (newForm) {
                            initCreateFormSubmit(newForm);
                        }
                    } else {
                        showMessage('error', data.message || '建立失敗');
                    }
                }
            })
            .catch(error => {
                console.error('Error submitting form:', error);
                showMessage('error', '提交失敗，請重試');
            });
    });
}

/**
 * 初始化專業分組表單提交
 */
function initDisciplineFormSubmit(form, projectId) {
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(form);

        // 檢查表單中是否有 discipline_id 隱藏欄位
        const disciplineIdInput = form.querySelector('input[name="discipline_id"]');
        let url;

        if (disciplineIdInput && disciplineIdInput.value) {
            // 更新模式
            const disciplineId = disciplineIdInput.value;
            url = `/budget/project/${projectId}/discipline/${disciplineId}/update-ajax/`;
        } else {
            // 創建模式
            url = `/budget/project/${projectId}/discipline/create-ajax/`;
        }

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 關閉 Modal
                    disciplineModal.close();

                    // 顯示成功訊息
                    showMessage('success', data.message || '專業分組已儲存');

                    // 重新載入頁面
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                } else {
                    // 顯示錯誤
                    if (data.html) {
                        disciplineModal.setContent(data.html);
                        // 重新初始化表單
                        const newForm = document.querySelector('#createDisciplineModal form');
                        if (newForm) {
                            initDisciplineFormSubmit(newForm, projectId);
                        }
                    } else {
                        showMessage('error', data.message || '建立失敗');
                    }
                }
            })
            .catch(error => {
                console.error('Error submitting form:', error);
                showMessage('error', '提交失敗，請重試');
            });
    });
}

/**
 * 顯示訊息（簡單實作）
 */
function showMessage(type, message) {
    // 可以整合到現有的 Django messages 系統
    console.log(`[${type}] ${message}`);
}

/**
 * 打開專業分組編輯 Modal
 */
function openDisciplineEditModal(projectId, disciplineId) {
    console.log('Opening discipline edit modal for project:', projectId, 'discipline:', disciplineId);

    disciplineModal.open();
    disciplineModal.showLoading();

    const url = `/budget-review/project/${projectId}/discipline/${disciplineId}/update-ajax/`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.html) {
                disciplineModal.setContent(data.html);

                // 初始化表單提交
                const form = disciplineModal.modal.querySelector('form');
                if (form) {
                    initDisciplineFormSubmit(form, projectId);
                }

                // 初始化可搜尋下拉選單
                const selectElements = disciplineModal.modal.querySelectorAll('.searchable-select');
                selectElements.forEach(select => {
                    if (typeof initializeSearchableSelect === 'function') {
                        initializeSearchableSelect(select);
                    }
                });
            } else {
                disciplineModal.setContent('<p class="error-text">載入表單失敗：無效的回應格式</p>');
            }
        })
        .catch(error => {
            console.error('Error loading discipline edit form:', error);
            disciplineModal.setContent('<p class="error-text">載入表單失敗，請重試。</p>');
        });
}

/**
 * 開啟文件上傳 Modal
 */
function openUploadModal(projectId, uploadType, disciplineId = null, budgetType = 'GROUP') {
    console.log('openUploadModal 被調用', { projectId, uploadType, disciplineId, budgetType });

    if (!uploadModal) {
        console.error('uploadModal 不存在！');
        return;
    }

    uploadModal.open();
    uploadModal.showLoading();

    let url = `/budget/project/${projectId}/upload/${uploadType}-ajax/`;
    const params = [];
    if (disciplineId) {
        params.push(`discipline=${disciplineId}`);
    }
    if (uploadType === 'budget' && budgetType) {
        params.push(`budget_type=${budgetType}`);
    }
    if (params.length > 0) {
        url += '?' + params.join('&');
    }

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.html) {
                uploadModal.setContent(data.html);

                // 初始化表單提交
                const form = document.querySelector('#uploadFileModal form');
                if (form) {
                    initUploadFormSubmit(form, projectId, uploadType);
                }
            } else {
                uploadModal.setContent('<p class="error-text">載入表單失敗：無效的回應格式</p>');
            }
        })
        .catch(error => {
            console.error('Error loading upload form:', error);
            uploadModal.setContent('<p class="error-text">載入表單失敗，請重試。</p>');
        });
}

/**
 * 初始化文件上傳表單提交
 */
function initUploadFormSubmit(form, projectId, uploadType) {
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        // 使用 FormData 處理文件上傳
        const formData = new FormData(form);

        fetch(`/budget/project/${projectId}/upload/${uploadType}-ajax/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    uploadModal.close();
                    alert(data.message || '檔案上傳成功');
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                } else {
                    alert(data.message || '上傳失敗');
                }
            })
            .catch(error => {
                console.error('Error uploading file:', error);
                alert('上傳失敗，請重試');
            });
    });
}

/**
 * 打開專業分組編輯 Modal  
 */
function openDisciplineEditModal(projectId, disciplineId) {
    console.log('Opening discipline edit modal for project:', projectId, 'discipline:', disciplineId);

    disciplineModal.open();
    disciplineModal.showLoading();

    const url = `/budget/project/${projectId}/discipline/${disciplineId}/update-ajax/`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.html) {
                disciplineModal.setContent(data.html);

                // 初始化表單提交
                const form = disciplineModal.modal.querySelector('form');
                if (form) {
                    initDisciplineFormSubmit(form, projectId);
                }

                // 初始化可搜尋下拉選單
                const selectElements = disciplineModal.modal.querySelectorAll('.searchable-select');
                selectElements.forEach(select => {
                    if (typeof initializeSearchableSelect === 'function') {
                        initializeSearchableSelect(select);
                    }
                });
            } else {
                disciplineModal.setContent('<p class="error-text">載入表單失敗：無效的回應格式</p>');
            }
        })
        .catch(error => {
            console.error('Error loading discipline edit form:', error);
            disciplineModal.setContent('<p class="error-text">載入表單失敗，請重試。</p>');
        });
}

/**
 * 刪除專業分組
 */
function deleteDiscipline(projectId, disciplineId) {
    if (!confirm('確定要刪除此專業分組嗎？相關提送紀錄將一併移除。')) {
        return;
    }

    fetch(`/budget/project/${projectId}/discipline/${disciplineId}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message || '刪除成功');
                closeCurrentModal();
                location.reload();
            } else {
                alert(data.message || '刪除失敗');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('發生錯誤');
        });
}
