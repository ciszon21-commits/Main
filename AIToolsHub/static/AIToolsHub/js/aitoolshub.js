// AI Tools Hub JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Initialize CSRF token for AJAX requests
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    // ===== Favorite & Like Toggle =====
    function setupActionButtons() {
        // Card action buttons
        document.querySelectorAll('.favorite-btn, .like-btn').forEach(btn => {
            btn.addEventListener('click', async function (e) {
                e.preventDefault();
                e.stopPropagation();

                const url = this.dataset.url;
                if (!url) return;

                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                            'Content-Type': 'application/json',
                        }
                    });

                    const data = await response.json();

                    if (data.success) {
                        this.classList.toggle('active');

                        // Update count if present
                        const countEl = this.querySelector('.action-count');
                        if (countEl && data.favorite_count !== undefined) {
                            countEl.textContent = data.favorite_count;
                        }
                        if (countEl && data.like_count !== undefined) {
                            countEl.textContent = data.like_count;
                        }

                        // Update text for large buttons
                        const textEl = this.querySelector('.action-text');
                        if (textEl) {
                            if (this.classList.contains('favorite-btn')) {
                                textEl.textContent = data.action === 'added' ? '已收藏' : '收藏';
                            } else if (this.classList.contains('like-btn')) {
                                textEl.textContent = data.action === 'added' ? '已點讚' : '點讚';
                            }
                        }

                        // If on favorites page and unfavorited, remove the card
                        if (window.location.pathname.includes('my-favorites') &&
                            this.classList.contains('favorite-btn') &&
                            data.action === 'removed') {
                            const card = this.closest('.tool-card');
                            if (card) {
                                card.style.opacity = '0';
                                card.style.transform = 'scale(0.8)';
                                setTimeout(() => card.remove(), 300);
                            }
                        }
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            });
        });
    }

    // ===== Comment Form =====
    function setupCommentForm() {
        const commentForm = document.getElementById('commentForm');
        if (!commentForm) return;

        commentForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const url = this.dataset.url;
            const formData = new FormData(this);

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                    },
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    // Add comment to list
                    const commentsList = document.getElementById('commentsList');
                    const noComments = commentsList.querySelector('.no-comments');
                    if (noComments) noComments.remove();

                    const anonymousBadge = data.comment.is_anonymous ? '<span class="anonymous-badge">匿名</span>' : '';
                    const newComment = document.createElement('div');
                    newComment.className = 'comment-item';
                    newComment.dataset.id = data.comment.id;
                    newComment.innerHTML = `
                        <div class="comment-header">
                            <span class="comment-author">${data.comment.user}${anonymousBadge}</span>
                            <span class="comment-date">${data.comment.created_at}</span>
                        </div>
                        <div class="comment-content" id="commentContent${data.comment.id}"><p>${data.comment.content}</p></div>
                        <div class="comment-reactions" data-comment-id="${data.comment.id}">
                            <button class="reaction-btn" data-reaction="like">👍 <span class="count">0</span></button>
                            <button class="reaction-btn" data-reaction="love">❤️</button>
                            <button class="reaction-btn" data-reaction="laugh">😄</button>
                            <button class="reaction-btn" data-reaction="wow">😮</button>
                        </div>
                        <div class="comment-actions-bar">
                            <button class="btn btn-link edit-comment-btn" data-comment-id="${data.comment.id}">編輯</button>
                            <button class="btn btn-link show-reply-btn" data-comment-id="${data.comment.id}">回覆</button>
                        </div>
                        <div class="comment-replies" id="replies${data.comment.id}"></div>
                    `;
                    commentsList.insertBefore(newComment, commentsList.firstChild);

                    // Clear form
                    this.querySelector('textarea').value = '';
                    const anonCheckbox = this.querySelector('input[name="is_anonymous"]');
                    if (anonCheckbox) anonCheckbox.checked = false;

                    // Update comment count
                    const countEl = document.querySelector('.comment-count');
                    if (countEl) {
                        const currentCount = parseInt(countEl.textContent.match(/\d+/)?.[0] || 0);
                        countEl.textContent = `(${currentCount + 1})`;
                    }

                    // Reinitialize event handlers
                    setupReplyForms();
                    setupEditForms();
                    setupReactionButtons();
                } else {
                    alert('留言失敗：' + (data.errors?.content?.[0] || '未知錯誤'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('留言失敗，請稍後再試');
            }
        });
    }

    // ===== Reply Form =====
    function setupReplyForms() {
        // Show reply form
        document.querySelectorAll('.show-reply-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                const commentItem = this.closest('.comment-item');
                const form = commentItem.querySelector('.reply-form');
                if (form) {
                    form.classList.remove('hidden');
                    form.querySelector('textarea').focus();
                }
            });
        });

        // Cancel reply
        document.querySelectorAll('.cancel-reply-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                const form = this.closest('.reply-form');
                form.classList.add('hidden');
                form.querySelector('textarea').value = '';
            });
        });

        // Submit reply
        document.querySelectorAll('.reply-form').forEach(form => {
            form.addEventListener('submit', async function (e) {
                e.preventDefault();

                const url = this.dataset.url;
                const formData = new FormData(this);

                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                        },
                        body: formData
                    });

                    const data = await response.json();

                    if (data.success) {
                        // Add reply to comment
                        const commentItem = this.closest('.comment-item');
                        const commentId = commentItem.dataset.id;
                        let repliesContainer = document.getElementById(`replies${commentId}`);

                        if (!repliesContainer) {
                            repliesContainer = document.createElement('div');
                            repliesContainer.className = 'comment-replies';
                            repliesContainer.id = `replies${commentId}`;
                            commentItem.appendChild(repliesContainer);
                        }

                        const anonymousBadge = data.reply.is_anonymous ? '<span class="anonymous-badge">匿名</span>' : '';
                        const ownerBadge = data.reply.is_tool_owner ? '<span class="owner-badge">上傳者</span>' : '';
                        const newReply = document.createElement('div');
                        newReply.className = 'reply-item';
                        newReply.dataset.id = data.reply.id;
                        newReply.innerHTML = `
                            <div class="reply-header">
                                <span class="reply-author">${data.reply.user}${anonymousBadge}${ownerBadge}</span>
                                <span class="reply-date">${data.reply.created_at}</span>
                            </div>
                            <div class="reply-content"><p>${data.reply.content}</p></div>
                        `;
                        repliesContainer.appendChild(newReply);

                        // Hide form and clear
                        this.classList.add('hidden');
                        this.querySelector('textarea').value = '';
                        const anonCheckbox = this.querySelector('input[name="is_anonymous"]');
                        if (anonCheckbox) anonCheckbox.checked = false;
                    } else {
                        alert('回覆失敗：' + (data.errors?.content?.[0] || data.error || '未知錯誤'));
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('回覆失敗，請稍後再試');
                }
            });
        });
    }

    // ===== Edit Comment =====
    function setupEditForms() {
        // Show edit form
        document.querySelectorAll('.edit-comment-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                const commentId = this.dataset.commentId;
                const contentEl = document.getElementById(`commentContent${commentId}`);
                const editForm = document.getElementById(`editForm${commentId}`);

                if (contentEl && editForm) {
                    contentEl.classList.add('hidden');
                    editForm.classList.remove('hidden');
                }
            });
        });

        // Cancel edit
        document.querySelectorAll('.cancel-edit-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                const editForm = this.closest('.edit-form');
                const commentItem = this.closest('.comment-item');
                const commentId = commentItem.dataset.id;
                const contentEl = document.getElementById(`commentContent${commentId}`);

                if (contentEl && editForm) {
                    editForm.classList.add('hidden');
                    contentEl.classList.remove('hidden');
                }
            });
        });

        // Submit edit
        document.querySelectorAll('.edit-form').forEach(form => {
            form.addEventListener('submit', async function (e) {
                e.preventDefault();

                const url = this.dataset.url;
                const formData = new FormData(this);

                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                        },
                        body: formData
                    });

                    const data = await response.json();

                    if (data.success) {
                        const commentItem = this.closest('.comment-item');
                        const commentId = commentItem.dataset.id;
                        const contentEl = document.getElementById(`commentContent${commentId}`);

                        // Update content
                        contentEl.innerHTML = `<p>${data.comment.content}</p>`;

                        // Hide form and show content
                        this.classList.add('hidden');
                        contentEl.classList.remove('hidden');
                    } else {
                        alert('編輯失敗：' + (data.errors?.content?.[0] || '未知錯誤'));
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('編輯失敗，請稍後再試');
                }
            });
        });
    }

    // ===== Reaction Buttons =====
    function setupReactionButtons() {
        document.querySelectorAll('.reaction-btn').forEach(btn => {
            btn.addEventListener('click', async function () {
                const url = this.dataset.url;
                const reactionType = this.dataset.reaction;

                if (!url) return;

                try {
                    const formData = new FormData();
                    formData.append('reaction_type', reactionType);

                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                        },
                        body: formData
                    });

                    const data = await response.json();

                    if (data.success) {
                        this.classList.toggle('active');

                        // Update counts in the reactions container
                        const container = this.closest('.comment-reactions');
                        container.querySelectorAll('.reaction-btn').forEach(rb => {
                            const rt = rb.dataset.reaction;
                            const countSpan = rb.querySelector('.count');
                            if (data.reaction_counts[rt] !== undefined) {
                                if (countSpan) {
                                    countSpan.textContent = data.reaction_counts[rt];
                                } else if (data.reaction_counts[rt] > 0) {
                                    rb.innerHTML = rb.innerHTML.split('<span')[0] + ` <span class="count">${data.reaction_counts[rt]}</span>`;
                                }
                            } else if (countSpan) {
                                countSpan.textContent = '0';
                            }
                        });
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            });
        });
    }

    // ===== Delete Buttons =====
    function setupDeleteButtons() {
        document.querySelectorAll('.delete-comment-btn').forEach(btn => {
            btn.addEventListener('click', async function () {
                if (!confirm('確定要刪除此留言嗎？刪除後將顯示為「此留言已被刪除」')) {
                    return;
                }

                const url = this.dataset.url;
                const commentId = this.dataset.commentId;

                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                        }
                    });

                    const data = await response.json();

                    if (data.success) {
                        const commentItem = this.closest('.comment-item');

                        // Mark as deleted
                        commentItem.classList.add('deleted');

                        // Update content
                        const contentEl = document.getElementById(`commentContent${commentId}`);
                        contentEl.classList.add('deleted-content');
                        contentEl.innerHTML = '<p class="deleted-text">此留言已被刪除</p>';

                        // Hide author name and add deleted icon
                        const authorEl = commentItem.querySelector('.comment-author');
                        authorEl.classList.add('deleted-author');
                        authorEl.innerHTML = `
                            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                                <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                            </svg>
                        `;

                        // Hide reactions, actions, edit form, reply form
                        const reactions = commentItem.querySelector('.comment-reactions');
                        const actionsBar = commentItem.querySelector('.comment-actions-bar');
                        const editForm = commentItem.querySelector('.edit-form');
                        const replyContainer = commentItem.querySelector('.reply-form-container');

                        if (reactions) reactions.style.display = 'none';
                        if (actionsBar) actionsBar.style.display = 'none';
                        if (editForm) editForm.style.display = 'none';
                        if (replyContainer) replyContainer.style.display = 'none';
                    } else {
                        alert('刪除失敗：' + (data.error || '未知錯誤'));
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('刪除失敗，請稍後再試');
                }
            });
        });
    }

    // Initialize all
    setupActionButtons();
    setupCommentForm();
    setupReplyForms();
    setupEditForms();
    setupReactionButtons();
    setupDeleteButtons();
});


