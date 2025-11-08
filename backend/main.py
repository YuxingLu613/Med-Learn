"""
Main FastAPI application for the surgical training multi-agent system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv

from agents import AgentOrchestrator
from scenario_engine import SurgicalScenario
from actions import get_actions_for_role, get_action_prompt

# Load environment variables
load_dotenv()

app = FastAPI(title="Surgical Training Multi-Agent System")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use proper state management)
orchestrator = AgentOrchestrator()
scenario: Optional[SurgicalScenario] = None


# Request/Response models
class StartScenarioRequest(BaseModel):
    procedure_name: str = "Appendectomy"


class ChatRequest(BaseModel):
    agent_type: str
    message: Optional[str] = None
    action_id: Optional[str] = None  # For structured actions


class ActionRequest(BaseModel):
    action: str


class ChatResponse(BaseModel):
    agent: str
    response: str
    complication: Optional[dict] = None
    failed: bool = False
    failure_reason: Optional[str] = None


class EvaluationRequest(BaseModel):
    procedure: str
    finalScore: int
    failed: bool
    complications: int
    interactions: int
    phasesCompleted: int
    duration: Optional[str] = None
    timeline: Optional[List[dict]] = None


class EvaluationResponse(BaseModel):
    overall_assessment: str
    key_observations: str
    recommendations: str
    strengths: List[str]
    improvements: List[str]


# API Endpoints
@app.get("/")
async def root():
    """Serve the landing page."""
    return FileResponse("frontend/landing.html")

@app.get("/landing.html")
async def landing():
    """Serve the landing page."""
    return FileResponse("frontend/landing.html")

@app.get("/simulator.html")
async def simulator():
    """Serve the simulator page."""
    return FileResponse("frontend/simulator.html")

@app.get("/dashboard.html")
async def dashboard():
    """Serve the dashboard page."""
    return FileResponse("frontend/dashboard.html")

@app.get("/summary.html")
async def summary():
    """Serve the summary page."""
    return FileResponse("frontend/summary.html")


@app.post("/api/scenario/start")
async def start_scenario(request: StartScenarioRequest):
    """Start a new surgical scenario."""
    global scenario
    scenario = SurgicalScenario(request.procedure_name)
    orchestrator.reset_all()

    return {
        "message": "Scenario started",
        "status": scenario.get_status()
    }


@app.get("/api/scenario/status")
async def get_scenario_status():
    """Get current scenario status."""
    if not scenario:
        raise HTTPException(status_code=400, detail="No active scenario")

    return scenario.get_status()


@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest) -> ChatResponse:
    """Send a message to a specific agent."""
    if not scenario:
        raise HTTPException(status_code=400, detail="No active scenario. Start a scenario first.")

    agent = orchestrator.get_agent(request.agent_type)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{request.agent_type}' not found")

    # Determine the message to send
    if request.action_id:
        # Use structured action
        user_message = get_action_prompt(request.action_id)
    elif request.message:
        # Use free-form message
        user_message = request.message
    else:
        raise HTTPException(status_code=400, detail="Either message or action_id must be provided")

    # Get agent response
    context = scenario.get_current_context()
    response = agent.respond(user_message, context)

    # Check if we should trigger a complication
    complication = None
    if scenario.should_trigger_complication():
        comp = scenario.trigger_complication()
        if comp:
            complication = {
                "name": comp.name,
                "description": comp.description,
                "severity": comp.severity.value
            }

    # Check for automatic phase advancement
    if scenario.check_phase_completion(request.action_id):
        scenario.advance_phase()
        scenario.auto_advanced = True

    # Check for failure conditions after interaction
    failure_reason = scenario.check_failure()

    return ChatResponse(
        agent=request.agent_type,
        response=response,
        complication=complication,
        failed=scenario.failed,
        failure_reason=failure_reason
    )


@app.post("/api/scenario/advance")
async def advance_phase():
    """Advance to the next phase of surgery."""
    if not scenario:
        raise HTTPException(status_code=400, detail="No active scenario")

    success = scenario.advance_phase()

    if not success:
        # Check completion
        completion = scenario.check_completion()
        return {
            "message": "Surgery completed",
            "completion": completion,
            "status": scenario.get_status()
        }

    return {
        "message": "Phase advanced",
        "status": scenario.get_status()
    }


@app.post("/api/scenario/resolve")
async def resolve_complication(request: ActionRequest):
    """Attempt to resolve a complication."""
    if not scenario:
        raise HTTPException(status_code=400, detail="No active scenario")

    # Simple resolution - in real system, would validate the action
    resolved = False
    for comp in scenario.active_complications:
        if scenario.resolve_complication(comp.name, request.action):
            resolved = True
            break

    return {
        "resolved": resolved,
        "status": scenario.get_status()
    }


@app.get("/api/agents")
async def get_agents():
    """Get list of available agents."""
    agents = orchestrator.get_available_agents()
    return {
        "agents": [
            {
                "type": agent_type,
                "name": orchestrator.get_agent(agent_type).role
            }
            for agent_type in agents
        ]
    }


@app.get("/api/actions/{agent_type}")
async def get_agent_actions(agent_type: str):
    """Get available actions for a specific agent type."""
    actions = get_actions_for_role(agent_type)
    if not actions:
        raise HTTPException(status_code=404, detail=f"No actions found for agent type '{agent_type}'")

    return {"actions": actions}


@app.post("/api/evaluate")
async def evaluate_performance(request: EvaluationRequest) -> EvaluationResponse:
    """Generate AI-powered evaluation of surgical performance."""
    from openai import OpenAI

    # Initialize DeepSeek client
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )

    # Create evaluation prompt
    prompt = f"""
You are an expert surgical instructor evaluating a trainee's performance in a surgical simulation.

Procedure: {request.procedure}
Final Score: {request.finalScore}/100
Status: {'Failed' if request.failed else 'Successful'}
Complications Handled: {request.complications}
Team Interactions: {request.interactions}
Phases Completed: {request.phasesCompleted}
Duration: {request.duration or 'N/A'}

Based on this performance data, provide a comprehensive evaluation with:

1. Overall Assessment (2-3 sentences about their overall performance)
2. Key Observations (2-3 specific observations about their decisions and actions)
3. Recommendations (2-3 actionable recommendations for improvement)
4. Strengths (list 2-4 specific things they did well)
5. Areas for Improvement (list 2-4 specific areas where they can improve)

Be constructive, professional, and specific. Format your response as:

OVERALL_ASSESSMENT: [your assessment]

KEY_OBSERVATIONS: [your observations]

RECOMMENDATIONS: [your recommendations]

STRENGTHS:
- [strength 1]
- [strength 2]
- [strength 3]

IMPROVEMENTS:
- [improvement 1]
- [improvement 2]
- [improvement 3]
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an expert surgical instructor providing detailed, constructive feedback."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )

        content = response.choices[0].message.content

        # Parse the response
        overall_assessment = ""
        key_observations = ""
        recommendations = ""
        strengths = []
        improvements = []

        # Simple parsing
        lines = content.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('OVERALL_ASSESSMENT:'):
                current_section = 'overall'
                overall_assessment = line.replace('OVERALL_ASSESSMENT:', '').strip()
            elif line.startswith('KEY_OBSERVATIONS:'):
                current_section = 'observations'
                key_observations = line.replace('KEY_OBSERVATIONS:', '').strip()
            elif line.startswith('RECOMMENDATIONS:'):
                current_section = 'recommendations'
                recommendations = line.replace('RECOMMENDATIONS:', '').strip()
            elif line.startswith('STRENGTHS:'):
                current_section = 'strengths'
            elif line.startswith('IMPROVEMENTS:'):
                current_section = 'improvements'
            elif line.startswith('- '):
                item = line.replace('- ', '').strip()
                if current_section == 'strengths':
                    strengths.append(item)
                elif current_section == 'improvements':
                    improvements.append(item)
            else:
                # Continue previous section
                if current_section == 'overall' and overall_assessment:
                    overall_assessment += ' ' + line
                elif current_section == 'observations' and key_observations:
                    key_observations += ' ' + line
                elif current_section == 'recommendations' and recommendations:
                    recommendations += ' ' + line

        # Ensure we have some content
        if not overall_assessment:
            overall_assessment = f"You completed the {request.procedure} with a score of {request.finalScore}/100."
        if not key_observations:
            key_observations = f"You handled {request.complications} complications and completed {request.phasesCompleted} phases."
        if not recommendations:
            recommendations = "Continue practicing to improve your surgical skills and decision-making abilities."
        if not strengths:
            strengths = ["Completed the simulation", "Gained valuable experience"]
        if not improvements:
            improvements = ["Practice more complex scenarios", "Work on team communication"]

        return EvaluationResponse(
            overall_assessment=overall_assessment,
            key_observations=key_observations,
            recommendations=recommendations,
            strengths=strengths,
            improvements=improvements
        )

    except Exception as e:
        # Fallback to basic evaluation if AI fails
        print(f"Error generating AI evaluation: {e}")

        strengths = []
        improvements = []

        if not request.failed:
            strengths.append("Successfully completed the surgical procedure")

        if request.finalScore >= 80:
            strengths.append("Maintained excellent performance throughout the surgery")

        if request.complications == 0:
            strengths.append("Avoided complications during the procedure")
        elif request.complications > 3:
            improvements.append("Focus on preventing and managing complications")

        if request.failed:
            improvements.append("Review critical decision-making points")
            improvements.append("Practice handling high-pressure situations")

        if request.finalScore < 70:
            improvements.append("Work on improving overall performance and technique")

        return EvaluationResponse(
            overall_assessment=f"You completed the {request.procedure} with a final score of {request.finalScore}/100. {'The surgery was successful.' if not request.failed else 'The surgery did not complete successfully.'}",
            key_observations=f"During this procedure, you had {request.interactions} team interactions and handled {request.complications} complications across {request.phasesCompleted} phases.",
            recommendations="Continue practicing similar procedures to build confidence and improve your surgical skills. Focus on team communication, decision-making speed, and crisis management.",
            strengths=strengths if strengths else ["Completed the simulation", "Gained valuable experience"],
            improvements=improvements if improvements else ["Continue practicing", "Work on team communication"]
        )


# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    print(f"""
    ╔═══════════════════════════════════════════════╗
    ║  Surgical Training Multi-Agent System         ║
    ║  Powered by DeepSeek AI                       ║
    ╚═══════════════════════════════════════════════╝

    Server running at: http://{host}:{port}

    Make sure you have set your DEEPSEEK_API_KEY in .env file
    """)

    uvicorn.run(app, host=host, port=port)
