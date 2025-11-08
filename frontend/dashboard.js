// Dashboard functionality

// Load session data from localStorage
function loadSessionData() {
    const sessions = JSON.parse(localStorage.getItem('surgicalSessions') || '[]');
    updateStatistics(sessions);
    populateSessionsTable(sessions);
}

// Update statistics cards
function updateStatistics(sessions) {
    const totalSessions = sessions.length;
    const successfulSurgeries = sessions.filter(s => !s.failed).length;
    const avgScore = sessions.length > 0
        ? Math.round(sessions.reduce((sum, s) => sum + (s.finalScore || 0), 0) / sessions.length)
        : 0;
    const proceduresCompleted = new Set(sessions.map(s => s.procedure)).size;

    document.getElementById('totalSessions').textContent = totalSessions;
    document.getElementById('successfulSurgeries').textContent = successfulSurgeries;
    document.getElementById('avgScore').textContent = avgScore;
    document.getElementById('proceduresCompleted').textContent = proceduresCompleted;
}

// Populate sessions table
function populateSessionsTable(sessions) {
    const tbody = document.getElementById('sessionsTableBody');

    if (sessions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 2rem; color: #7f8c8d;">
                    No training sessions yet. <a href="/simulator.html" style="color: #27ae60;">Start your first simulation</a>
                </td>
            </tr>
        `;
        return;
    }

    // Sort by date (newest first)
    sessions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    tbody.innerHTML = sessions.map((session, index) => {
        const date = new Date(session.timestamp).toLocaleDateString();
        const score = session.finalScore || 0;
        const scoreBadgeClass = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low';
        const statusBadge = session.failed
            ? '<span class="status-badge failed">✗ Failed</span>'
            : '<span class="status-badge success">✓ Successful</span>';
        const duration = session.duration || 'N/A';

        return `
            <tr>
                <td>${date}</td>
                <td>${session.procedure}</td>
                <td><span class="score-badge ${scoreBadgeClass}">${score}</span></td>
                <td>${statusBadge}</td>
                <td>${duration}</td>
                <td>
                    <button class="btn-small btn-view" onclick="viewSummary(${index})">View Summary</button>
                </td>
            </tr>
        `;
    }).join('');
}

// View session summary
function viewSummary(sessionIndex) {
    const sessions = JSON.parse(localStorage.getItem('surgicalSessions') || '[]');
    const session = sessions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[sessionIndex];

    if (session) {
        // Store the session to view in localStorage
        localStorage.setItem('currentSessionSummary', JSON.stringify(session));
        // Navigate to summary page
        window.location.href = '/summary.html';
    }
}

// Filter sessions
function filterSessions() {
    const procedureFilter = document.getElementById('filterProcedure').value;
    const statusFilter = document.getElementById('filterStatus').value;

    let sessions = JSON.parse(localStorage.getItem('surgicalSessions') || '[]');

    if (procedureFilter !== 'all') {
        // Filter by procedure category
        const categoryMap = {
            'general': ['Appendectomy', 'Cholecystectomy', 'Hernia Repair', 'Bowel Resection', 'Mastectomy'],
            'orthopedic': ['Hip Replacement', 'Knee Arthroscopy', 'Spinal Fusion', 'Fracture Fixation'],
            'cardiovascular': ['Coronary Artery Bypass', 'Valve Replacement', 'Pacemaker Insertion'],
            'dental': ['Wisdom Tooth Extraction', 'Dental Implant', 'Root Canal', 'Apicoectomy', 'Gingivectomy', 'Jaw Surgery']
        };

        sessions = sessions.filter(s => categoryMap[procedureFilter]?.some(p => s.procedure.includes(p)));
    }

    if (statusFilter !== 'all') {
        const showSuccess = statusFilter === 'success';
        sessions = sessions.filter(s => !s.failed === showSuccess);
    }

    populateSessionsTable(sessions);
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadSessionData();

    // Add filter listeners
    document.getElementById('filterProcedure')?.addEventListener('change', filterSessions);
    document.getElementById('filterStatus')?.addEventListener('change', filterSessions);
});

// Activity chart placeholder
const canvas = document.getElementById('activityChart');
if (canvas) {
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#7f8c8d';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Activity chart coming soon', canvas.width / 2, canvas.height / 2);
}
