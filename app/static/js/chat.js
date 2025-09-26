// static/js/chat.js
let chatMessages = [];

// Load chat messages from localStorage when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadChatFromStorage();
    scrollToBottom();
});

// Function to load messages from localStorage
function loadChatFromStorage() {
    const savedMessages = localStorage.getItem('chatMessages');
    if (savedMessages) {
        try {
            chatMessages = JSON.parse(savedMessages);
            displayChatMessages();
        } catch (e) {
            console.error('Error loading chat messages:', e);
            chatMessages = [];
        }
    }
}

// Function to display all chat messages
function displayChatMessages() {
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) return;
    
    chatContainer.innerHTML = '';
    
    chatMessages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.sender}`;
        
        messageDiv.innerHTML = `
            <div class="message-content">${msg.text}</div>
            <div class="message-time">${msg.time}</div>
        `;
        
        chatContainer.appendChild(messageDiv);
    });
    
    scrollToBottom();
}

// Function to add a message to chat
function addMessageToChat(text, sender) {
    const message = {
        text: text,
        sender: sender,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    
    chatMessages.push(message);
    localStorage.setItem('chatMessages', JSON.stringify(chatMessages));
    
    // If chat container is visible, update it
    displayChatMessages();
}

// Function to scroll to bottom of chat
function scrollToBottom() {
    const chatContainer = document.getElementById('chatMessages');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Save chat before page unload
window.addEventListener('beforeunload', function() {
    localStorage.setItem('chatMessages', JSON.stringify(chatMessages));
});