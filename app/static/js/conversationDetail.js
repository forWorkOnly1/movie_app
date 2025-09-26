// app/static/js/conversationDetail.js

document.addEventListener('DOMContentLoaded', function() {
    // Delete conversation button
    const deleteBtn = document.getElementById('deleteConversationBtn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            const conversationId = this.getAttribute('data-conversation-id');
            deleteConversation(conversationId);
        });
    }

    // Clear messages button
    const clearMessagesBtn = document.getElementById('clearMessagesBtn');
    if (clearMessagesBtn) {
        clearMessagesBtn.addEventListener('click', function() {
            const conversationId = this.getAttribute('data-conversation-id');
            clearMessages(conversationId);
        });
    }
});

function deleteConversation(conversationId) {
    if (confirm('Are you sure you want to delete this conversation?')) {
        fetch(`/delete_conversation/${conversationId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Conversation deleted successfully!', 'success');
                // Redirect to chat history after success
                setTimeout(() => {
                    window.location.href = '/conversations';
                }, 1000);
            } else {
                showAlert('Error deleting conversation: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error deleting conversation', 'error');
        });
    }
}

function clearMessages(conversationId) {
    if (confirm('Are you sure you want to clear all messages in this conversation?')) {
        fetch(`/clear_messages/${conversationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Messages cleared successfully!', 'success');
                // Reload the page
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showAlert('Error clearing messages: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error clearing messages', 'error');
        });
    }
}

function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
    alertDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}