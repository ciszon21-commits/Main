// Comment form submission (AJAX)
document.addEventListener('DOMContentLoaded', function () {
    const commentForm = document.getElementById('commentForm');

    if (commentForm) {
        commentForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const formData = new FormData(commentForm);
            const submitButton = commentForm.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;

            // Disable button and show loading state
            submitButton.disabled = true;
            submitButton.textContent = '送出中...';

            try {
                const response = await fetch(`/showcase/achievement/${achievementId}/comment/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                    },
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    // Clear form
                    commentForm.reset();

                    // Add new comment to list
                    const commentsList = document.getElementById('commentsList');
                    const noComments = commentsList.querySelector('.no-comments');

                    if (noComments) {
                        noComments.remove();
                    }

                    const newComment = document.createElement('div');
                    newComment.className = 'comment-item';
                    newComment.style.animation = 'fadeInUp 0.5s ease';
                    newComment.innerHTML = `
                        <div class="comment-header">
                            <div class="comment-avatar">${data.comment.user.charAt(0)}</div>
                            <div class="comment-info">
                                <strong>${data.comment.user}</strong>
                                <span class="comment-time">${data.comment.created_at}</span>
                            </div>
                        </div>
                        <div class="comment-content">${data.comment.content}</div>
                    `;

                    commentsList.insertBefore(newComment, commentsList.firstChild);

                    // Show success message
                    showNotification('留言已送出，開發者將收到郵件通知', 'success');
                } else {
                    // Show error
                    const errors = Object.values(data.errors).flat().join(', ');
                    showNotification(errors, 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification('送出失敗，請稍後再試', 'error');
            } finally {
                // Re-enable button
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    }
});

// Notification function
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#48bb78' : '#f56565'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        animation: slideInRight 0.3s ease;
        max-width: 400px;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add notification animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});
