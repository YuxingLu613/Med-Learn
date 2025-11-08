// Summary page functionality

let currentSession = null;

// Load session data
function loadSessionData() {
    const sessionData = localStorage.getItem('currentSessionSummary');

    if (!sessionData) {
        // No session to display
        document.querySelector('.summary-container').innerHTML = `
            <div style="text-align: center; padding: 4rem;">
                <h2>No session data available</h2>
                <p>Please complete a surgery simulation first.</p>
                <a href="/simulator.html" class="btn btn-primary">Start Training</a>
            </div>
        `;
        return;
    }

    currentSession = JSON.parse(sessionData);
    populateHeader();
    populateOverview();
    populateSkillRatings();
    populateTimeline();
    generateAIEvaluation();
}

// Populate header section
function populateHeader() {
    const { procedure, timestamp, finalScore, failed } = currentSession;

    document.getElementById('procedureName').textContent = procedure || 'Unknown Procedure';
    document.getElementById('procedureDate').textContent = new Date(timestamp).toLocaleString();
    document.getElementById('overallScore').textContent = finalScore || 0;

    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');

    if (failed) {
        statusIndicator.classList.add('failed');
        statusText.textContent = '✗ Surgery Failed';
    } else {
        statusIndicator.classList.add('success');
        statusText.textContent = '✓ Surgery Successful';
    }

    // Color-code the score
    const scoreValue = document.getElementById('overallScore');
    const score = finalScore || 0;
    if (score >= 80) {
        scoreValue.style.color = '#27ae60';
    } else if (score >= 60) {
        scoreValue.style.color = '#f39c12';
    } else {
        scoreValue.style.color = '#e74c3c';
    }
}

// Populate performance overview
function populateOverview() {
    const { duration, interactions, complications, phasesCompleted } = currentSession;

    document.getElementById('duration').textContent = duration || 'N/A';
    document.getElementById('interactions').textContent = interactions || 0;
    document.getElementById('complications').textContent = complications || 0;
    document.getElementById('phasesCompleted').textContent = phasesCompleted || 0;
}

// Populate skill ratings
function populateSkillRatings() {
    const { finalScore, failed, complications } = currentSession;

    // Calculate skill scores based on performance
    const baseScore = finalScore || 0;

    // Communication: based on score and interactions
    const commScore = Math.min(100, Math.max(0, baseScore + (failed ? -10 : 5)));

    // Decision Making: heavily influenced by success/failure
    const decisionScore = Math.min(100, Math.max(0, failed ? baseScore - 20 : baseScore + 10));

    // Crisis Management: based on complications handled
    const crisisScore = Math.min(100, Math.max(0, baseScore - (complications || 0) * 5));

    // Team Coordination: based on overall performance
    const teamScore = Math.min(100, Math.max(0, baseScore));

    // Update UI
    updateSkill('comm', commScore);
    updateSkill('decision', decisionScore);
    updateSkill('crisis', crisisScore);
    updateSkill('team', teamScore);
}

function updateSkill(skillId, score) {
    document.getElementById(`${skillId}Score`).textContent = `${score}/100`;
    setTimeout(() => {
        document.getElementById(`${skillId}Bar`).style.width = `${score}%`;
    }, 100);
}

// Populate timeline
function populateTimeline() {
    const { timeline } = currentSession;
    const timelineContainer = document.getElementById('timeline');

    if (!timeline || timeline.length === 0) {
        timelineContainer.innerHTML = '<p style="color: #7f8c8d; text-align: center;">No timeline data available</p>';
        return;
    }

    timelineContainer.innerHTML = timeline.map(item => {
        const isComplication = item.type === 'complication';
        return `
            <div class="timeline-item ${isComplication ? 'complication' : ''}">
                <div class="timeline-phase">${item.phase || 'Unknown Phase'}</div>
                <div class="timeline-time">${item.time || 'N/A'}</div>
                <div class="timeline-description">${item.description || ''}</div>
                ${isComplication ? `<div class="timeline-complication">⚠️ ${item.complication}</div>` : ''}
            </div>
        `;
    }).join('');
}

// Generate AI evaluation
async function generateAIEvaluation() {
    const evaluationContent = document.getElementById('evaluationContent');

    try {
        const response = await fetch('/api/evaluate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(currentSession)
        });

        if (!response.ok) {
            throw new Error('Failed to generate evaluation');
        }

        const data = await response.json();

        // Display evaluation
        evaluationContent.innerHTML = `
            <div class="evaluation-section">
                <h3>Overall Assessment</h3>
                <p>${data.overall_assessment || 'Your performance was evaluated successfully.'}</p>
            </div>
            <div class="evaluation-section">
                <h3>Key Observations</h3>
                <p>${data.key_observations || 'N/A'}</p>
            </div>
            <div class="evaluation-section">
                <h3>Recommendations</h3>
                <p>${data.recommendations || 'Continue practicing to improve your skills.'}</p>
            </div>
        `;

        // Update strengths and improvements
        if (data.strengths) {
            const strengthsList = document.getElementById('strengthsList');
            strengthsList.innerHTML = data.strengths.map(s => `<li>${s}</li>`).join('');
        }

        if (data.improvements) {
            const improvementsList = document.getElementById('improvementsList');
            improvementsList.innerHTML = data.improvements.map(i => `<li>${i}</li>`).join('');
        }

    } catch (error) {
        console.error('Error generating evaluation:', error);

        // Fallback to basic evaluation
        const { finalScore, failed, complications } = currentSession;

        const strengths = [];
        const improvements = [];

        if (!failed) {
            strengths.push('Successfully completed the surgical procedure');
        }

        if (finalScore >= 80) {
            strengths.push('Maintained excellent performance throughout');
        } else if (finalScore >= 60) {
            improvements.push('Work on improving overall performance score');
        }

        if (complications > 2) {
            improvements.push('Focus on preventing and managing complications more effectively');
        } else if (complications === 0) {
            strengths.push('Avoided complications during the procedure');
        }

        if (failed) {
            improvements.push('Review critical decision-making points that led to surgery failure');
            improvements.push('Practice handling high-pressure situations');
        }

        // Add some general recommendations
        if (strengths.length === 0) {
            strengths.push('Attempted the procedure and gained valuable experience');
        }

        if (improvements.length === 0) {
            improvements.push('Continue practicing to refine your skills');
        }

        evaluationContent.innerHTML = `
            <div class="evaluation-section">
                <h3>Overall Assessment</h3>
                <p>${failed ? 'The surgery did not complete successfully. Review the areas for improvement below and try again.' : 'Congratulations on completing the surgery! Review the feedback below to continue improving.'}</p>
            </div>
            <div class="evaluation-section">
                <h3>Key Observations</h3>
                <p>Final score: ${finalScore}/100. You handled ${complications || 0} complication(s) during the procedure.</p>
            </div>
            <div class="evaluation-section">
                <h3>Recommendations</h3>
                <p>Focus on team communication, decision-making speed, and crisis management skills. Practice similar procedures to build confidence and muscle memory.</p>
            </div>
        `;

        document.getElementById('strengthsList').innerHTML = strengths.map(s => `<li>${s}</li>`).join('');
        document.getElementById('improvementsList').innerHTML = improvements.map(i => `<li>${i}</li>`).join('');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', loadSessionData);
