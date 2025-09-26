// app/static/js/chatHistory.js

console.log('🚀 chatHistory.js loaded successfully!');

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM fully loaded');

    // Clear All Chats button
    const clearAllBtn = document.getElementById('clearAllChatsBtn');
    if (clearAllBtn) {
        console.log('✅ Found Clear All button');
        clearAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🎯 Clear All button clicked');
            clearAllChats();
        });
    } else {
        console.log('❌ Clear All button NOT found');
    }

    // Event delegation for delete buttons
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.delete-conversation-btn');
        if (!btn) return;

        e.preventDefault();
        const conversationId = btn.getAttribute('data-conversation-id');
        console.log('🎯 Delete button clicked for:', conversationId);
        deleteConversation(conversationId, btn);
    });
});

function deleteConversation(conversationId, button) {
    if (!conversationId || !button) return;

    if (!confirm('Are you sure you want to delete this conversation?')) return;

    button.innerHTML = '⏳ Deleting...';
    button.disabled = true;

    fetch(`/delete_conversation/${conversationId}`, { method: 'DELETE' })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            return res.json();
        })
        .then(data => {
            if (data.success) {
                showAlert('✅ Conversation deleted successfully!', 'success');
                const item = button.closest('.conversation-item');
                if (item) {
                    // Smooth removal animation
                    item.style.transition = 'all 0.3s ease';
                    item.style.opacity = '0';
                    item.style.height = '0';
                    item.style.padding = '0';
                    item.style.margin = '0';
                    item.style.overflow = 'hidden';

                    setTimeout(() => {
                        item.remove();
                        // Reload if no conversations left
                        if (document.querySelectorAll('.conversation-item').length === 0) {
                            window.location.reload();
                        }
                    }, 300);
                }
            } else {
                button.innerHTML = '🗑️ Delete';
                button.disabled = false;
                showAlert('❌ Error: ' + (data.error || 'Unknown error'), 'error');
            }
        })
        .catch(err => {
            console.error('💥 Fetch error:', err);
            button.innerHTML = '🗑️ Delete';
            button.disabled = false;
            showAlert('❌ Network error. Please try again.', 'error');
        });
}

function clearAllChats() {
    const button = document.getElementById('clearAllChatsBtn');
    if (!button || !confirm('Are you sure you want to delete ALL your chat history?')) return;

    button.innerHTML = '⏳ Clearing all chats...';
    button.disabled = true;

    fetch('/clear_chats', { method: 'POST' })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            return res.json();
        })
        .then(data => {
            if (data.success) {
                showAlert(`✅ Cleared ${data.deleted_count || 'all'} conversations!`, 'success');
                // Reload page to reflect cleared chats
                setTimeout(() => window.location.reload(), 500);
            } else {
                showAlert('❌ Error: ' + (data.error || 'Unknown error'), 'error');
                button.innerHTML = '🗑️ Clear All Chats';
                button.disabled = false;
            }
        })
        .catch(err => {
            console.error('💥 Clear all fetch error:', err);
            button.innerHTML = '🗑️ Clear All Chats';
            button.disabled = false;
            showAlert('❌ Network error. Please try again.', 'error');
        });
}

function showAlert(message, type) {
    document.querySelectorAll('.custom-alert').forEach(a => a.remove());
    const alertDiv = document.createElement('div');
    alertDiv.className = `custom-alert alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
    alertDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}

// For debugging
window.testChatHistory = function() {
    console.log('🧪 Testing chatHistory.js...');
    console.log('Clear All button:', document.getElementById('clearAllChatsBtn'));
    console.log('Delete buttons:', document.querySelectorAll('.delete-conversation-btn').length);
    return 'Test complete!';
};
