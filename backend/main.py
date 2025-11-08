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


# API Endpoints
@app.get("/")
async def root():
    """Serve the frontend."""
    return FileResponse("frontend/index.html")


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
