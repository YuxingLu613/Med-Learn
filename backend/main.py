"""
Main FastAPI application for the surgical training multi-agent system.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from datetime import timedelta

from agents import AgentOrchestrator
from scenario_engine import SurgicalScenario
from actions import get_actions_for_role, get_action_prompt
from database import get_db, init_db, User, TrainingSession
from auth import verify_password, get_password_hash, create_access_token, decode_access_token

# Load environment variables
load_dotenv()

app = FastAPI(title="MedLearn - Surgical Training Platform")

# Initialize database
init_db()

# Security
security = HTTPBearer()

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
# Change to dict to support multiple users
scenarios: dict = {}  # user_id -> SurgicalScenario


# Helper function to get current user from token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


# Request/Response models
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]


class StartScenarioRequest(BaseModel):
    procedure_name: str = "Appendectomy"


class ChatRequest(BaseModel):
    agent_type: str
    message: Optional[str] = None
    action_id: Optional[str] = None  # For structured actions


class ActionRequest(BaseModel):
    action: str


class SaveSessionRequest(BaseModel):
    procedure: str
    timestamp: str
    duration: Optional[str]
    finalScore: int
    failed: bool
    complications: int
    interactions: int
    phasesCompleted: int
    timeline: List[dict]


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

# Authentication endpoints
@app.post("/api/auth/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(request.password)
    new_user = User(
        username=request.username,
        email=request.email,
        hashed_password=hashed_password,
        full_name=request.full_name
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create access token
    access_token = create_access_token(data={"sub": new_user.username})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name
        }
    )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user."""
    user = db.query(User).filter(User.username == request.username).first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.username})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    )


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name
    )


# Page routes
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

@app.get("/login.html")
async def login_page():
    """Serve the login page."""
    return FileResponse("frontend/login.html")

@app.get("/register.html")
async def register_page():
    """Serve the registration page."""
    return FileResponse("frontend/register.html")


# Scenario endpoints (protected)
@app.post("/api/scenario/start")
async def start_scenario(
    request: StartScenarioRequest,
    current_user: User = Depends(get_current_user)
):
    """Start a new surgical scenario for the current user."""
    scenario = SurgicalScenario(request.procedure_name)
    orchestrator.reset_all()

    # Store scenario for this user
    scenarios[current_user.id] = scenario

    return {
        "message": "Scenario started",
        "status": scenario.get_status()
    }


@app.get("/api/scenario/status")
async def get_scenario_status(current_user: User = Depends(get_current_user)):
    """Get current scenario status for the current user."""
    scenario = scenarios.get(current_user.id)
    if not scenario:
        raise HTTPException(status_code=400, detail="No active scenario")

    return scenario.get_status()


@app.post("/api/chat")
async def chat_with_agent(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """Send a message to a specific agent."""
    scenario = scenarios.get(current_user.id)
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
async def advance_phase(current_user: User = Depends(get_current_user)):
    """Advance to the next phase of surgery."""
    scenario = scenarios.get(current_user.id)
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
async def resolve_complication(
    request: ActionRequest,
    current_user: User = Depends(get_current_user)
):
    """Attempt to resolve a complication."""
    scenario = scenarios.get(current_user.id)
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


# Session management endpoints
@app.post("/api/sessions/save")
async def save_session(
    request: SaveSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a training session to the database."""
    from datetime import datetime as dt

    session = TrainingSession(
        user_id=current_user.id,
        procedure=request.procedure,
        timestamp=dt.fromisoformat(request.timestamp.replace('Z', '+00:00')),
        duration=request.duration,
        final_score=request.finalScore,
        failed=request.failed,
        complications=request.complications,
        interactions=request.interactions,
        phases_completed=request.phasesCompleted,
        timeline=request.timeline  # Will be automatically converted to JSON
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return {"message": "Session saved successfully", "session_id": session.id}


@app.get("/api/sessions")
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all training sessions for the current user."""
    sessions = db.query(TrainingSession).filter(
        TrainingSession.user_id == current_user.id
    ).order_by(TrainingSession.timestamp.desc()).all()

    return {
        "sessions": [
            {
                "id": s.id,
                "procedure": s.procedure,
                "timestamp": s.timestamp.isoformat(),
                "duration": s.duration,
                "finalScore": s.final_score,
                "failed": s.failed,
                "complications": s.complications,
                "interactions": s.interactions,
                "phasesCompleted": s.phases_completed,
                "timeline": s.timeline
            }
            for s in sessions
        ]
    }


@app.get("/api/sessions/{session_id}")
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific training session."""
    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": session.id,
        "procedure": session.procedure,
        "timestamp": session.timestamp.isoformat(),
        "duration": session.duration,
        "finalScore": session.final_score,
        "failed": session.failed,
        "complications": session.complications,
        "interactions": session.interactions,
        "phasesCompleted": session.phases_completed,
        "timeline": session.timeline
    }


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
