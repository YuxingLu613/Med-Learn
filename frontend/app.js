// API base URL
const API_BASE = window.location.origin;

// State
let currentAgent = null;
let scenarioActive = false;

// DOM Elements
const startBtn = document.getElementById('startBtn');
const advanceBtn = document.getElementById('advanceBtn');
const sendBtn = document.getElementById('sendBtn');
const messageInput = document.getElementById('messageInput');
const chatMessages = document.getElementById('chatMessages');
const procedureSelect = document.getElementById('procedure');
const scenarioStatus = document.getElementById('scenarioStatus');
const currentPhase = document.getElementById('currentPhase');
const successScore = document.getElementById('successScore');
const complicationsSection = document.getElementById('complications');
const complicationsList = document.getElementById('complicationsList');
const selectedAgentDiv = document.getElementById('selectedAgent');
const completionPanel = document.getElementById('completionPanel');
const completionResults = document.getElementById('completionResults');

// Event Listeners
startBtn.addEventListener('click', startScenario);
advanceBtn.addEventListener('click', advancePhase);
sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !sendBtn.disabled) {
        sendMessage();
    }
});

// Agent selection
document.querySelectorAll('.agent-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const agentType = btn.dataset.agent;
        selectAgent(agentType);

        // Update UI
        document.querySelectorAll('.agent-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });
});

// Functions
async function startScenario() {
    const procedure = procedureSelect.value;

    try {
        startBtn.disabled = true;
        startBtn.textContent = 'Starting...';

        const response = await fetch(`${API_BASE}/api/scenario/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ procedure_name: procedure })
        });

        const data = await response.json();

        scenarioActive = true;
        scenarioStatus.style.display = 'block';
        complicationsSection.style.display = 'block';
        completionPanel.style.display = 'none';

        updateStatus(data.status);

        // Clear chat
        chatMessages.innerHTML = `
            <div class="message message-agent">
                <div class="message-bubble">
                    <div class="message-header">System</div>
                    <strong>Surgery Started: ${procedure}</strong><br>
                    The team is ready. Select a team member and begin communicating.
                </div>
            </div>
        `;

        startBtn.textContent = 'Restart Surgery';
        startBtn.disabled = false;

        // Enable input if agent selected
        if (currentAgent) {
            messageInput.disabled = false;
            sendBtn.disabled = false;
        }

    } catch (error) {
        console.error('Error starting scenario:', error);
        alert('Failed to start scenario. Make sure the backend is running.');
        startBtn.disabled = false;
        startBtn.textContent = 'Start Surgery';
    }
}

async function advancePhase() {
    try {
        advanceBtn.disabled = true;
        advanceBtn.textContent = 'Advancing...';

        const response = await fetch(`${API_BASE}/api/scenario/advance`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.completion && data.completion.completed) {
            // Surgery completed
            showCompletion(data.completion);
            scenarioActive = false;
            messageInput.disabled = true;
            sendBtn.disabled = true;
        } else {
            updateStatus(data.status);
            addSystemMessage(`Advanced to: ${data.status.phase.replace('_', ' ').toUpperCase()}`);
        }

        advanceBtn.textContent = 'Advance Phase →';
        advanceBtn.disabled = false;

    } catch (error) {
        console.error('Error advancing phase:', error);
        advanceBtn.textContent = 'Advance Phase →';
        advanceBtn.disabled = false;
    }
}

async function sendMessage() {
    if (!currentAgent || !scenarioActive) return;

    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage('user', message, 'You');

    // Clear input
    messageInput.value = '';
    messageInput.disabled = true;
    sendBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent_type: currentAgent,
                message: message
            })
        });

        const data = await response.json();

        // Add agent response
        addMessage('agent', data.response, getAgentName(currentAgent));

        // Check for complications
        if (data.complication) {
            showComplicationAlert(data.complication);
            // Refresh status to show new complication
            await refreshStatus();
        }

    } catch (error) {
        console.error('Error sending message:', error);
        addSystemMessage('Error: Failed to communicate with agent.');
    } finally {
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

function selectAgent(agentType) {
    currentAgent = agentType;
    selectedAgentDiv.textContent = `Communicating with: ${getAgentName(agentType)}`;

    if (scenarioActive) {
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

function addMessage(type, text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;

    messageDiv.innerHTML = `
        <div class="message-bubble">
            <div class="message-header">${sender}</div>
            ${text}
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-agent';

    messageDiv.innerHTML = `
        <div class="message-bubble">
            <div class="message-header">System</div>
            <strong>${text}</strong>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showComplicationAlert(complication) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'complication-alert';

    alertDiv.innerHTML = `
        <h4>⚠️ COMPLICATION DETECTED</h4>
        <strong>${complication.name}</strong>
        <p>${complication.description}</p>
        <span class="severity severity-${complication.severity}">${complication.severity}</span>
    `;

    chatMessages.appendChild(alertDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function updateStatus(status) {
    currentPhase.textContent = status.phase.replace('_', ' ').toUpperCase();
    successScore.textContent = status.success_score;

    // Update score color
    if (status.success_score >= 70) {
        successScore.style.color = '#48bb78';
    } else if (status.success_score >= 50) {
        successScore.style.color = '#ed8936';
    } else {
        successScore.style.color = '#f56565';
    }

    // Update complications
    if (status.active_complications && status.active_complications.length > 0) {
        complicationsList.innerHTML = status.active_complications.map(comp => `
            <div class="complication-item">
                <h4>${comp.name}</h4>
                <p>${comp.description}</p>
                <span class="severity severity-${comp.severity}">${comp.severity}</span>
                <button class="resolve-btn" onclick="resolveComplication('${comp.name}')">
                    Mark Resolved
                </button>
            </div>
        `).join('');
    } else {
        complicationsList.innerHTML = '<p style="color: #666; font-size: 0.9rem;">No active complications</p>';
    }
}

async function refreshStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/scenario/status`);
        const status = await response.json();
        updateStatus(status);
    } catch (error) {
        console.error('Error refreshing status:', error);
    }
}

async function resolveComplication(compName) {
    try {
        const action = prompt(`How are you resolving "${compName}"?`);
        if (!action) return;

        const response = await fetch(`${API_BASE}/api/scenario/resolve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });

        const data = await response.json();

        if (data.resolved) {
            addSystemMessage(`Complication resolved: ${compName}`);
            updateStatus(data.status);
        }

    } catch (error) {
        console.error('Error resolving complication:', error);
    }
}

function showCompletion(completion) {
    completionPanel.style.display = 'block';

    const resultClass = completion.success ? 'success' : 'failure';
    const emoji = completion.success ? '✅' : '❌';

    completionResults.innerHTML = `
        <div class="completion-result">
            <h4>${emoji} ${completion.success ? 'Surgery Successful!' : 'Surgery Failed'}</h4>
        </div>
        <div class="completion-result">
            <strong>Final Score:</strong> ${completion.score}/100
        </div>
        <div class="completion-result">
            <strong>Complications Resolved:</strong> ${completion.complications_resolved}
        </div>
        <div class="completion-result">
            <strong>Complications Unresolved:</strong> ${completion.complications_unresolved}
        </div>
        <div class="completion-result" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #ccc;">
            ${completion.summary}
        </div>
    `;

    addSystemMessage(`Surgery completed with score: ${completion.score}/100`);
}

function getAgentName(agentType) {
    const names = {
        'nurse': '👩‍⚕️ Surgical Nurse',
        'anesthetist': '💉 Anesthetist',
        'patient': '🛏️ Patient',
        'assistant': '👨‍⚕️ Surgical Assistant'
    };
    return names[agentType] || agentType;
}

// Make resolveComplication available globally
window.resolveComplication = resolveComplication;
