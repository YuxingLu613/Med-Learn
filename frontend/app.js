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
const vitalsMonitor = document.getElementById('vitalsMonitor');
const heartRate = document.getElementById('heartRate');
const bloodPressure = document.getElementById('bloodPressure');
const oxygenSat = document.getElementById('oxygenSat');
const temperature = document.getElementById('temperature');

// Vitals state
let vitalsInterval = null;
const baseVitals = {
    hr: 72,
    bp: {systolic: 120, diastolic: 80},
    spo2: 98,
    temp: 37.0
};

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
        vitalsMonitor.style.display = 'block';
        completionPanel.style.display = 'none';

        updateStatus(data.status);
        startVitalsMonitoring();

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

// Vitals monitoring functions
function startVitalsMonitoring() {
    if (vitalsInterval) {
        clearInterval(vitalsInterval);
    }

    // Update vitals every 3 seconds with slight variations
    vitalsInterval = setInterval(updateVitals, 3000);
    updateVitals(); // Initial update
}

function stopVitalsMonitoring() {
    if (vitalsInterval) {
        clearInterval(vitalsInterval);
        vitalsInterval = null;
    }
}

function updateVitals() {
    // Add slight random variations to make it realistic
    const hr = baseVitals.hr + Math.floor(Math.random() * 6 - 3); // ±3 bpm
    const systolic = baseVitals.bp.systolic + Math.floor(Math.random() * 10 - 5);
    const diastolic = baseVitals.bp.diastolic + Math.floor(Math.random() * 6 - 3);
    const spo2 = Math.min(100, baseVitals.spo2 + Math.floor(Math.random() * 3 - 1));
    const temp = (baseVitals.temp + (Math.random() * 0.4 - 0.2)).toFixed(1);

    // Update display
    heartRate.textContent = `${hr} bpm`;
    bloodPressure.textContent = `${systolic}/${diastolic}`;
    oxygenSat.textContent = `${spo2}%`;
    temperature.textContent = `${temp}°C`;

    // Apply warning/critical classes
    heartRate.className = 'vital-value';
    bloodPressure.className = 'vital-value';
    oxygenSat.className = 'vital-value';
    temperature.className = 'vital-value';

    if (hr < 60 || hr > 100) heartRate.className = 'vital-value warning';
    if (hr < 50 || hr > 120) heartRate.className = 'vital-value critical';

    if (systolic > 140 || systolic < 100) bloodPressure.className = 'vital-value warning';
    if (systolic > 160 || systolic < 90) bloodPressure.className = 'vital-value critical';

    if (spo2 < 95) oxygenSat.className = 'vital-value warning';
    if (spo2 < 92) oxygenSat.className = 'vital-value critical';

    if (temp > 37.5 || temp < 36.5) temperature.className = 'vital-value warning';
    if (temp > 38.0 || temp < 36.0) temperature.className = 'vital-value critical';
}

// Make resolveComplication available globally
window.resolveComplication = resolveComplication;
