// static/js/chat-handler.js
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
});

function initializeChat() {
    const chatInput = document.getElementById('chatText');
    const chatSend = document.getElementById('chatSend');
    
    // Set up event listeners only if elements exist
    if (chatSend) {
        chatSend.addEventListener('click', sendMessage);
    }
    
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Auto-resize textarea
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
}

async function sendMessage() {
    const chatInput = document.getElementById('chatText');
    const chatMessages = document.getElementById('chatMessages');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat immediately
    addMessageToChat(message, 'user');
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot';
    typingDiv.textContent = 'Typing...';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // Remove typing indicator and add actual response
        typingDiv.remove();
        if (data.reply) {
            addMessageToChat(data.reply, 'bot');
        }
        
    } catch (error) {
        console.error('Error:', error);
        typingDiv.textContent = 'Sorry, I encountered an error. Please try again.';
    }
}