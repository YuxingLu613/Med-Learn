// API base URL
const API_BASE = window.location.origin;

// State
let currentAgent = null;
let scenarioActive = false;

// DOM Elements
const startBtn = document.getElementById('startBtn');
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
const patientStatus = document.getElementById('patientStatus');
const actionButtons = document.getElementById('actionButtons');
const actionButtonsList = document.getElementById('actionButtonsList');
const phaseAdvanceNotification = document.getElementById('phaseAdvanceNotification');

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

// Function to show phase advancement notification
function showPhaseAdvanceNotification() {
    phaseAdvanceNotification.style.display = 'block';

    // Auto-hide after 3 seconds (matching the animation duration)
    setTimeout(() => {
        phaseAdvanceNotification.style.display = 'none';
    }, 3000);
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

        // Check for failure
        if (data.failed) {
            showFailure(data.failure_reason);
            scenarioActive = false;
            messageInput.disabled = true;
            sendBtn.disabled = true;
            stopVitalsMonitoring();
            return;
        }

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
        if (scenarioActive) {
            messageInput.disabled = false;
            sendBtn.disabled = false;
            messageInput.focus();
        }
    }
}

async function selectAgent(agentType) {
    currentAgent = agentType;
    selectedAgentDiv.textContent = `Communicating with: ${getAgentName(agentType)}`;

    if (scenarioActive) {
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();

        // Load actions for this agent
        await loadActionsForAgent(agentType);
    }
}

async function loadActionsForAgent(agentType) {
    try {
        const response = await fetch(`${API_BASE}/api/actions/${agentType}`);
        const data = await response.json();

        // Display action buttons
        actionButtonsList.innerHTML = '';
        data.actions.forEach(action => {
            const btn = document.createElement('button');
            btn.className = 'action-btn';
            btn.textContent = action.label;
            btn.title = action.description;
            btn.onclick = () => sendAction(action.id, action.label);
            actionButtonsList.appendChild(btn);
        });

        actionButtons.style.display = 'block';
    } catch (error) {
        console.error('Error loading actions:', error);
        actionButtons.style.display = 'none';
    }
}

async function sendAction(actionId, actionLabel) {
    if (!currentAgent || !scenarioActive) return;

    // Add action to chat as user message
    addMessage('user', `[Action: ${actionLabel}]`, 'You');

    // Disable buttons temporarily
    const buttons = actionButtonsList.querySelectorAll('.action-btn');
    buttons.forEach(btn => btn.disabled = true);
    messageInput.disabled = true;
    sendBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent_type: currentAgent,
                action_id: actionId
            })
        });

        const data = await response.json();

        // Add agent response
        addMessage('agent', data.response, getAgentName(currentAgent));

        // Check for failure
        if (data.failed) {
            showFailure(data.failure_reason);
            scenarioActive = false;
            messageInput.disabled = true;
            sendBtn.disabled = true;
            actionButtons.style.display = 'none';
            stopVitalsMonitoring();
            return;
        }

        // Check for complications
        if (data.complication) {
            showComplicationAlert(data.complication);
            await refreshStatus();
        }

    } catch (error) {
        console.error('Error sending action:', error);
        addSystemMessage('Error: Failed to execute action.');
    } finally {
        if (scenarioActive) {
            buttons.forEach(btn => btn.disabled = false);
            messageInput.disabled = false;
            sendBtn.disabled = false;
        }
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

    // Check for automatic phase advancement
    if (status.auto_advanced) {
        showPhaseAdvanceNotification();
        addSystemMessage(`✨ Phase automatically advanced to: ${status.phase.replace('_', ' ').toUpperCase()}`);
    }

    // Update patient status
    if (status.patient_status) {
        patientStatus.textContent = status.patient_status;

        // Color code based on status
        if (status.patient_status.includes('CRITICAL') || status.patient_status.includes('Failed')) {
            patientStatus.style.color = '#c62828';
            patientStatus.style.fontWeight = 'bold';
        } else if (status.patient_status.includes('Unstable') || status.patient_status.includes('Guarded')) {
            patientStatus.style.color = '#f57c00';
            patientStatus.style.fontWeight = 'bold';
        } else if (status.patient_status.includes('Fair')) {
            patientStatus.style.color = '#fbc02d';
        } else {
            patientStatus.style.color = '#088395';
            patientStatus.style.fontWeight = 'normal';
        }
    }

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

    // Update vitals based on complications
    adjustVitalsForComplications(status.active_complications || []);
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
            addSystemMessage(`Complication resolved: ${compName} - Patient stabilizing.`);
            updateStatus(data.status);
            // Vitals will automatically update via adjustVitalsForComplications in updateStatus
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

function showFailure(reason) {
    completionPanel.style.display = 'block';
    completionPanel.style.background = '#fee';
    completionPanel.style.borderColor = '#f44336';

    completionResults.innerHTML = `
        <div class="completion-result">
            <h4 style="color: #c62828;">❌ SURGERY FAILED</h4>
        </div>
        <div class="completion-result">
            <strong>Reason:</strong> ${reason}
        </div>
        <div class="completion-result">
            <strong>Final Score:</strong> 0/100
        </div>
        <div class="completion-result" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #ccc; color: #c62828;">
            Critical mistakes led to surgery failure. Review the procedure and try again.
        </div>
    `;

    // Show dramatic failure message in chat
    const failureDiv = document.createElement('div');
    failureDiv.className = 'complication-alert';
    failureDiv.style.background = '#ffebee';
    failureDiv.style.borderColor = '#f44336';

    failureDiv.innerHTML = `
        <h4 style="color: #c62828;">🚨 SURGERY FAILED</h4>
        <strong>${reason}</strong>
        <p style="margin-top: 8px;">The surgery has been terminated.</p>
    `;

    chatMessages.appendChild(failureDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
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

// Adjust vitals based on active complications
function adjustVitalsForComplications(complications) {
    // Reset to normal baseline
    baseVitals.hr = 72;
    baseVitals.bp.systolic = 120;
    baseVitals.bp.diastolic = 80;
    baseVitals.spo2 = 98;
    baseVitals.temp = 37.0;

    // Apply modifications based on each active complication
    complications.forEach(comp => {
        const name = comp.name.toLowerCase();

        // Blood pressure complications
        if (name.includes('blood pressure drop') || name.includes('hypotension')) {
            baseVitals.bp.systolic = 85;
            baseVitals.bp.diastolic = 55;
            baseVitals.hr = 105; // Compensatory tachycardia
        }
        else if (name.includes('blood pressure spike') || name.includes('hypertension')) {
            baseVitals.bp.systolic = 180;
            baseVitals.bp.diastolic = 110;
        }

        // Oxygen complications
        if (name.includes('oxygen saturation drop') || name.includes('hypoxia')) {
            baseVitals.spo2 = 88;
            baseVitals.hr = 95; // Tachycardia from hypoxia
        }

        // Cardiac complications
        if (name.includes('arrhythmia')) {
            baseVitals.hr = 135; // Irregular rapid heart rate
        }

        // Bleeding complications
        if (name.includes('bleeding') || name.includes('hemorrhage')) {
            baseVitals.hr = 110; // Tachycardia from blood loss
            baseVitals.bp.systolic = 95; // Dropping BP
            baseVitals.bp.diastolic = 60;
        }

        // Anxiety/stress
        if (name.includes('anxiety')) {
            baseVitals.hr = 95;
            baseVitals.bp.systolic = 135;
            baseVitals.bp.diastolic = 88;
        }

        // Allergic reaction
        if (name.includes('allergic')) {
            baseVitals.hr = 100;
            baseVitals.bp.systolic = 100;
            baseVitals.spo2 = 93;
        }

        // Difficult intubation/airway issues
        if (name.includes('intubation') || name.includes('airway')) {
            baseVitals.spo2 = 91;
            baseVitals.hr = 105;
        }

        // Temperature
        if (name.includes('fever') || name.includes('infection')) {
            baseVitals.temp = 38.5;
        }
    });

    // Immediately update display with new values
    updateVitals();
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
