// Chat state
let conversationHistory = [];
const REQUEST_TIMEOUT_MS = 130000;
const HISTORY_LIMIT = 6;

// DOM Elements
const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const clearButton = document.getElementById('clearButton');
const loadingIndicator = document.getElementById('loading');
const modelSelect = document.getElementById('modelSelect');
const modelDropdown = document.getElementById('modelDropdown');
const modelDropdownButton = document.getElementById('modelDropdownButton');
const modelDropdownLabel = document.getElementById('modelDropdownLabel');
const modelDropdownMenu = document.getElementById('modelDropdownMenu');
const ragEnabled = document.getElementById('ragEnabled');
const webEnabled = document.getElementById('webEnabled');
const ragStatus = document.getElementById('ragStatus');

// Auto-resize textarea
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
});

// Send message on Enter (Shift+Enter for new line)
userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendButton.addEventListener('click', sendMessage);
clearButton.addEventListener('click', clearChat);
modelDropdownButton.addEventListener('click', toggleModelDropdown);

function setModelControlDisabled(disabled) {
    modelSelect.disabled = disabled;
    modelDropdownButton.disabled = disabled;
    if (disabled) {
        closeModelDropdown();
    }
}

function toggleModelDropdown() {
    if (modelDropdownButton.disabled) return;
    const isOpen = modelDropdown.classList.contains('open');
    if (isOpen) {
        closeModelDropdown();
    } else {
        modelDropdown.classList.add('open');
        modelDropdownButton.setAttribute('aria-expanded', 'true');
    }
}

function closeModelDropdown() {
    modelDropdown.classList.remove('open');
    modelDropdownButton.setAttribute('aria-expanded', 'false');
}

function selectModel(name) {
    modelSelect.value = name;
    modelDropdownLabel.textContent = name;

    Array.from(modelDropdownMenu.querySelectorAll('.model-dropdown-item')).forEach((item) => {
        item.classList.toggle('active', item.dataset.value === name);
    });

    closeModelDropdown();
}

function renderModelDropdown(models, selectedModel) {
    modelDropdownMenu.innerHTML = '';

    models.forEach((name) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'model-dropdown-item';
        button.dataset.value = name;
        button.textContent = name;
        if (name === selectedModel) {
            button.classList.add('active');
        }
        button.addEventListener('click', () => selectModel(name));
        modelDropdownMenu.appendChild(button);
    });

    modelDropdownLabel.textContent = selectedModel || 'Select model';
}

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();
        const models = data.models || [];

        modelSelect.innerHTML = '';
        models.forEach((name) => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            if (name === data.default) {
                option.selected = true;
            }
            modelSelect.appendChild(option);
        });

        const selectedModel = modelSelect.value || models[0] || '';
        renderModelDropdown(models, selectedModel);
    } catch (error) {
        console.error('Failed to load models', error);
        modelDropdownLabel.textContent = 'Unavailable';
    }
}

async function refreshRagStatus() {
    try {
        const response = await fetch('/api/rag/status');
        const data = await response.json();
        const documentCount = data.document_count || 0;
        const chunkCount = data.chunk_count || 0;
        ragStatus.textContent = `RAG: ${documentCount} documents loaded (${chunkCount} chunks)`;
    } catch (error) {
        ragStatus.textContent = 'RAG: status unavailable';
    }
}

async function refreshWebStatus() {
    try {
        const response = await fetch('/api/web/status');
        const data = await response.json();
        if (!data.configured) {
            webEnabled.checked = false;
            webEnabled.disabled = true;
            webEnabled.title = 'Set GOOGLE_API_KEY and GOOGLE_CSE_ID to enable Web Mode';
        }
    } catch (error) {
        webEnabled.checked = false;
        webEnabled.disabled = true;
        webEnabled.title = 'Web status unavailable';
    }
}

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    userInput.disabled = true;
    sendButton.disabled = true;
    setModelControlDisabled(true);
    ragEnabled.disabled = true;
    webEnabled.disabled = true;
    loadingIndicator.style.display = 'block';

    addMessage(message, 'user');

    conversationHistory.push({
        role: 'user',
        content: message,
    });

    userInput.value = '';
    userInput.style.height = 'auto';

    const botMessageTextDiv = addMessage('', 'bot');

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: controller.signal,
            body: JSON.stringify({
                message,
                model: modelSelect.value,
                rag_enabled: ragEnabled.checked,
                web_enabled: webEnabled.checked,
                history: conversationHistory.slice(-HISTORY_LIMIT),
            }),
        });

        clearTimeout(timeoutId);

        if (!response.ok || !response.body) {
            throw new Error('Stream unavailable');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let assistantMessage = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.trim()) continue;

                let event;
                try {
                    event = JSON.parse(line);
                } catch {
                    continue;
                }

                if (event.type === 'token') {
                    assistantMessage += event.content;
                    botMessageTextDiv.innerHTML = formatMessage(assistantMessage);
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                } else if (event.type === 'error') {
                    throw new Error(event.error || 'Stream error');
                } else if (event.type === 'done') {
                    if (event.rag_enabled) {
                        refreshRagStatus();
                    }
                }
            }
        }

        if (!assistantMessage.trim()) {
            assistantMessage = 'Sorry, I could not generate a response.';
            botMessageTextDiv.innerHTML = formatMessage(assistantMessage);
        }

        conversationHistory.push({
            role: 'assistant',
            content: assistantMessage,
        });
    } catch (error) {
        console.error('Error:', error);
        const fallback = error.name === 'AbortError'
            ? 'The request took too long. Please try a shorter question.'
            : 'Sorry, I could not connect to the server. Please try again.';
        botMessageTextDiv.innerHTML = formatMessage(fallback);
        conversationHistory.push({ role: 'assistant', content: fallback });
    } finally {
        userInput.disabled = false;
        sendButton.disabled = false;
        setModelControlDisabled(false);
        ragEnabled.disabled = false;
        if (webEnabled.title !== 'Set GOOGLE_API_KEY and GOOGLE_CSE_ID to enable Web Mode' && webEnabled.title !== 'Web status unavailable') {
            webEnabled.disabled = false;
        }
        loadingIndicator.style.display = 'none';
        userInput.focus();
    }
}

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = `message-avatar ${sender}-avatar`;
    avatarDiv.innerHTML = sender === 'bot'
        ? '<i class="fas fa-robot"></i>'
        : '<i class="fas fa-user"></i>';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.innerHTML = formatMessage(text);

    contentDiv.appendChild(textDiv);
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    return textDiv;
}

function formatMessage(text) {
    text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\n/g, '<br>');
    return text;
}

function clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        conversationHistory = [];
        messagesContainer.innerHTML = '';

        const welcomeMessage = `👋 Hello! I'm your AI assistant. I can help you with:
        <ul>
            <li>Technology & Programming</li>
            <li>Science & Mathematics</li>
            <li>Business & Finance</li>
            <li>Arts & Literature</li>
            <li>Health & Wellness</li>
            <li>General Knowledge & More</li>
        </ul>
        Ask me anything! 🚀`;

        addMessage(welcomeMessage, 'bot');
    }
}

window.addEventListener('load', async () => {
    userInput.focus();
    await loadModels();
    await refreshRagStatus();
    await refreshWebStatus();
});

document.addEventListener('click', (event) => {
    if (!modelDropdown.contains(event.target)) {
        closeModelDropdown();
    }
});

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeModelDropdown();
    }
});
