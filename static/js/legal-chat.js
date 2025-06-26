/**
 * Legal Chat System for document analysis results
 */

class LegalChatSystem {
    constructor() {
        this.chatContainer = null;
        this.messageContainer = null;
        this.inputField = null;
        this.sendButton = null;
        this.isInitialized = false;
        this.analysisContext = '';
        this.conversationHistory = [];
    }

    initialize(analysisContext = '') {
        if (this.isInitialized) return;
        
        this.analysisContext = analysisContext;
        this.createChatInterface();
        this.attachEventListeners();
        this.addWelcomeMessage();
        this.isInitialized = true;
    }

    createChatInterface() {
        // Create chat container
        const chatHTML = `
            <div class="legal-chat-container" id="legalChat">
                <div class="chat-header">
                    <div class="chat-title">
                        <i class="bi bi-chat-dots"></i>
                        <span>Asistent Legal - Întrebări despre Documentul Dvs.</span>
                    </div>
                    <button class="chat-toggle" id="chatToggle">
                        <i class="bi bi-chevron-up"></i>
                    </button>
                </div>
                <div class="chat-body" id="chatBody">
                    <div class="chat-messages" id="chatMessages">
                        <!-- Messages will be added here -->
                    </div>
                    <div class="chat-input-container">
                        <div class="quick-questions">
                            <button class="quick-question-btn" data-question="Care sunt obligațiile mele din acest document?">
                                Obligațiile mele
                            </button>
                            <button class="quick-question-btn" data-question="Există riscuri legale pe care trebuie să le știu?">
                                Riscuri legale
                            </button>
                            <button class="quick-question-btn" data-question="Ce termene trebuie să respect?">
                                Termene importante
                            </button>
                        </div>
                        <div class="chat-input-wrapper">
                            <input type="text" id="chatInput" placeholder="Întreabă orice despre aspectele legale ale documentului..." maxlength="500">
                            <button id="sendMessage" disabled>
                                <i class="bi bi-send"></i>
                            </button>
                        </div>
                        <div class="chat-disclaimer">
                            <small>⚠️ Acest chat oferă informații generale. Pentru sfaturi legale specifice, consultați un avocat.</small>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .legal-chat-container {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 400px;
                max-width: 90vw;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                z-index: 1000;
                border: 1px solid #e0e0e0;
                overflow: hidden;
                transition: all 0.3s ease;
            }

            .legal-chat-container.minimized .chat-body {
                display: none;
            }

            .chat-header {
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: white;
                padding: 15px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
            }

            .chat-title {
                display: flex;
                align-items: center;
                font-weight: 600;
                font-size: 14px;
            }

            .chat-title i {
                margin-right: 8px;
                font-size: 16px;
            }

            .chat-toggle {
                background: none;
                border: none;
                color: white;
                font-size: 16px;
                cursor: pointer;
                padding: 5px;
                border-radius: 5px;
                transition: background-color 0.2s ease;
            }

            .chat-toggle:hover {
                background: rgba(255, 255, 255, 0.1);
            }

            .chat-body {
                max-height: 500px;
                display: flex;
                flex-direction: column;
            }

            .chat-messages {
                flex: 1;
                padding: 20px;
                max-height: 300px;
                overflow-y: auto;
                background: #f8f9fa;
            }

            .chat-message {
                margin-bottom: 15px;
                display: flex;
                flex-direction: column;
            }

            .chat-message.user {
                align-items: flex-end;
            }

            .chat-message.assistant {
                align-items: flex-start;
            }

            .message-bubble {
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 18px;
                word-wrap: break-word;
                font-size: 14px;
                line-height: 1.4;
            }

            .chat-message.user .message-bubble {
                background: #007bff;
                color: white;
                border-bottom-right-radius: 5px;
            }

            .chat-message.assistant .message-bubble {
                background: white;
                color: #333;
                border: 1px solid #e0e0e0;
                border-bottom-left-radius: 5px;
            }

            .message-time {
                font-size: 11px;
                color: #666;
                margin-top: 5px;
                padding: 0 5px;
            }

            .quick-questions {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                padding: 15px 20px 10px;
                background: white;
                border-top: 1px solid #e0e0e0;
            }

            .quick-question-btn {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                color: #495057;
                padding: 8px 12px;
                border-radius: 20px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                white-space: nowrap;
            }

            .quick-question-btn:hover {
                background: #007bff;
                color: white;
                border-color: #007bff;
            }

            .chat-input-wrapper {
                display: flex;
                padding: 15px 20px;
                background: white;
                align-items: center;
                gap: 10px;
            }

            #chatInput {
                flex: 1;
                border: 1px solid #ddd;
                border-radius: 25px;
                padding: 12px 16px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s ease;
            }

            #chatInput:focus {
                border-color: #007bff;
            }

            #sendMessage {
                background: #007bff;
                border: none;
                color: white;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background-color 0.2s ease;
            }

            #sendMessage:disabled {
                background: #ccc;
                cursor: not-allowed;
            }

            #sendMessage:not(:disabled):hover {
                background: #0056b3;
            }

            .chat-disclaimer {
                padding: 10px 20px;
                background: #fff3cd;
                border-top: 1px solid #ffeaa7;
                text-align: center;
            }

            .typing-indicator {
                display: flex;
                align-items: center;
                padding: 12px 16px;
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 18px;
                border-bottom-left-radius: 5px;
                max-width: 80%;
            }

            .typing-dots {
                display: flex;
                gap: 4px;
            }

            .typing-dot {
                width: 6px;
                height: 6px;
                background: #666;
                border-radius: 50%;
                animation: typingAnimation 1.4s infinite ease-in-out;
            }

            .typing-dot:nth-child(2) {
                animation-delay: 0.2s;
            }

            .typing-dot:nth-child(3) {
                animation-delay: 0.4s;
            }

            @keyframes typingAnimation {
                0%, 60%, 100% {
                    transform: translateY(0);
                    opacity: 0.3;
                }
                30% {
                    transform: translateY(-10px);
                    opacity: 1;
                }
            }

            @media (max-width: 768px) {
                .legal-chat-container {
                    width: 100%;
                    bottom: 0;
                    right: 0;
                    left: 0;
                    border-radius: 15px 15px 0 0;
                }

                .quick-questions {
                    flex-direction: column;
                }

                .quick-question-btn {
                    white-space: normal;
                    text-align: left;
                }
            }
        `;
        document.head.appendChild(style);

        // Add chat to page
        document.body.insertAdjacentHTML('beforeend', chatHTML);

        // Get references
        this.chatContainer = document.getElementById('legalChat');
        this.messageContainer = document.getElementById('chatMessages');
        this.inputField = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendMessage');
    }

    attachEventListeners() {
        // Chat toggle
        document.getElementById('chatToggle').addEventListener('click', () => {
            this.chatContainer.classList.toggle('minimized');
            const icon = document.querySelector('#chatToggle i');
            icon.className = this.chatContainer.classList.contains('minimized') 
                ? 'bi bi-chevron-down' 
                : 'bi bi-chevron-up';
        });

        // Input field
        this.inputField.addEventListener('input', () => {
            this.sendButton.disabled = this.inputField.value.trim().length === 0;
        });

        this.inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.sendButton.disabled) {
                this.sendMessage();
            }
        });

        // Send button
        this.sendButton.addEventListener('click', () => {
            if (!this.sendButton.disabled) {
                this.sendMessage();
            }
        });

        // Quick questions
        document.querySelectorAll('.quick-question-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const question = btn.dataset.question;
                this.inputField.value = question;
                this.sendButton.disabled = false;
                this.sendMessage();
            });
        });

        // Header click to toggle
        document.querySelector('.chat-header').addEventListener('click', (e) => {
            if (e.target !== document.getElementById('chatToggle') && !e.target.closest('#chatToggle')) {
                document.getElementById('chatToggle').click();
            }
        });
    }

    addWelcomeMessage() {
        const welcomeMessage = `
            Bună! Sunt asistentul dvs. legal virtual. Pot răspunde la întrebări despre documentul analizat.
            
            Exemple de întrebări:
            • Care sunt obligațiile mele principale?
            • Există clauze problematice?
            • Ce termene trebuie să respect?
            • Care sunt riscurile legale?
        `;
        
        this.addMessage(welcomeMessage, 'assistant');
    }

    addMessage(content, sender = 'user') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        
        const time = new Date().toLocaleTimeString('ro-RO', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        messageDiv.innerHTML = `
            <div class="message-bubble">${content}</div>
            <div class="message-time">${time}</div>
        `;

        this.messageContainer.appendChild(messageDiv);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }

    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message assistant typing-message';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        this.messageContainer.appendChild(typingDiv);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
        
        return typingDiv;
    }

    removeTypingIndicator() {
        const typingMessage = this.messageContainer.querySelector('.typing-message');
        if (typingMessage) {
            typingMessage.remove();
        }
    }

    async sendMessage() {
        const message = this.inputField.value.trim();
        if (!message) return;

        // Add user message
        this.addMessage(message, 'user');
        this.conversationHistory.push({ role: 'user', content: message });

        // Clear input
        this.inputField.value = '';
        this.sendButton.disabled = true;

        // Show typing indicator
        const typingIndicator = this.showTypingIndicator();

        try {
            // Send to backend
            const response = await fetch('/legal-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    analysis_context: this.analysisContext,
                    conversation_history: this.conversationHistory.slice(-6) // Last 6 messages for context
                })
            });

            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator();

            if (data.success) {
                this.addMessage(data.response, 'assistant');
                this.conversationHistory.push({ role: 'assistant', content: data.response });
            } else {
                this.addMessage('Ne pare rău, a apărut o eroare. Vă rugăm să încercați din nou.', 'assistant');
            }

        } catch (error) {
            this.removeTypingIndicator();
            this.addMessage('Ne pare rău, nu pot răspunde momentan. Vă rugăm să încercați din nou.', 'assistant');
            console.error('Chat error:', error);
        }
    }
}

// Initialize chat when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on result pages
    if (window.location.pathname.includes('/success') || document.querySelector('.analysis-result')) {
        // Get analysis context from page
        const analysisElement = document.querySelector('.analysis-content, .result-content');
        const analysisContext = analysisElement ? analysisElement.textContent : '';
        
        // Initialize chat system
        window.legalChat = new LegalChatSystem();
        
        // Delay initialization to ensure page is fully loaded
        setTimeout(() => {
            window.legalChat.initialize(analysisContext);
        }, 1000);
    }
});