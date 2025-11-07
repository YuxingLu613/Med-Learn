# 🏥 Surgical Training Multi-Agent System

An interactive web-based surgical training simulator powered by AI agents. Clinicians can practice surgical scenarios, communicate with different operating room team members (nurses, anesthetists, patients, assistants), and handle unexpected complications in a realistic training environment.

## Features

- **Multi-Agent System**: Interact with AI-powered agents representing different roles:
  - 👩‍⚕️ Surgical Nurse
  - 💉 Anesthetist
  - 🛏️ Patient
  - 👨‍⚕️ Surgical Assistant

- **Realistic Scenarios**: Practice different surgical procedures with realistic workflow phases:
  - Pre-operative preparation
  - Anesthesia induction
  - Incision
  - Main procedure
  - Closing
  - Post-operative care

- **Dynamic Complications**: Random complications arise during surgery that require quick decision-making:
  - Unexpected bleeding
  - Blood pressure drops
  - Allergic reactions
  - Oxygen saturation issues
  - Equipment problems

- **Performance Tracking**: Get scored on your performance based on:
  - How well you handle complications
  - Communication with team members
  - Successful completion of surgery phases

## Tech Stack

- **Backend**: Python, FastAPI
- **AI**: Anthropic Claude API (multi-agent system)
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **API**: RESTful endpoints with JSON

## Prerequisites

- Python 3.8 or higher
- Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))
- pip (Python package manager)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Med-Learn
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_actual_api_key_here
   ```

## Running the Application

1. **Start the backend server**:
   ```bash
   python backend/main.py
   ```

   The server will start at `http://localhost:8000`

2. **Open your browser**:
   Navigate to `http://localhost:8000`

3. **Start training**:
   - Select a surgical procedure (Appendectomy, Cholecystectomy, etc.)
   - Click "Start Surgery"
   - Select a team member to communicate with
   - Type messages to interact with the agents
   - Handle complications as they arise
   - Advance through surgical phases
   - Complete the surgery!

## How to Use

### Starting a Scenario

1. Choose a procedure from the dropdown
2. Click "Start Surgery"
3. The scenario begins in the pre-operative phase

### Communicating with Agents

1. Click on any team member button (Nurse, Anesthetist, Patient, Assistant)
2. Type your message in the chat input
3. The AI agent will respond based on their role and the current scenario
4. Different agents have different expertise and perspectives

### Handling Complications

- Complications appear randomly during the surgery
- They're shown in the "Active Complications" panel
- Respond appropriately by:
  - Communicating with relevant team members
  - Taking appropriate actions
  - Marking complications as resolved when handled

### Advancing Phases

- Click "Advance Phase →" to move through surgical stages
- Make sure you're ready before advancing
- Handle any active complications first for better scores

### Scoring

- Start with 100 points
- Lose points when complications occur (-10)
- Lose points for unresolved complications (-20 each at end)
- Gain points for resolving complications (+5)
- Final score determines success (≥50 = successful surgery)

## Project Structure

```
Med-Learn/
├── backend/
│   ├── main.py              # FastAPI application and routes
│   ├── agents.py            # AI agent implementations
│   └── scenario_engine.py   # Scenario management and logic
├── frontend/
│   ├── index.html           # Main UI
│   ├── style.css            # Styling
│   └── app.js               # Frontend logic
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## API Endpoints

### Start Scenario
```http
POST /api/scenario/start
Content-Type: application/json

{
  "procedure_name": "Appendectomy"
}
```

### Get Scenario Status
```http
GET /api/scenario/status
```

### Chat with Agent
```http
POST /api/chat
Content-Type: application/json

{
  "agent_type": "nurse",
  "message": "What are the patient's vitals?"
}
```

### Advance Phase
```http
POST /api/scenario/advance
```

### Resolve Complication
```http
POST /api/scenario/resolve
Content-Type: application/json

{
  "action": "Applied pressure and cauterized bleeding vessel"
}
```

### Get Available Agents
```http
GET /api/agents
```

## Development

### Adding New Agents

Edit `backend/agents.py` and create a new agent class:

```python
class NewRoleAgent(SurgicalAgent):
    def __init__(self):
        super().__init__(
            role="Role Name",
            personality="Description of personality",
            expertise="Areas of expertise"
        )
```

Then register it in the `AgentOrchestrator` class.

### Adding New Complications

Edit `backend/scenario_engine.py` and add to the `COMPLICATIONS` list:

```python
Complication(
    "Complication Name",
    "Description of what's happening",
    ComplicationSeverity.MODERATE,
    SurgeryPhase.PROCEDURE
)
```

### Adding New Procedures

Currently procedures are for display only. To add custom logic per procedure, extend the `SurgicalScenario` class.

## Future Enhancements

- [ ] Voice input/output for hands-free operation
- [ ] More surgical procedures with specialized workflows
- [ ] Multiplayer mode (trainee + supervisor)
- [ ] Video/animation of surgical procedures
- [ ] Performance analytics and progress tracking
- [ ] Customizable difficulty levels
- [ ] Integration with medical training curricula
- [ ] VR/AR support for immersive training

## Troubleshooting

**Issue**: "No API key provided"
- **Solution**: Make sure you've created a `.env` file with your `ANTHROPIC_API_KEY`

**Issue**: "Connection refused" when opening browser
- **Solution**: Ensure the backend server is running (`python backend/main.py`)

**Issue**: Agents not responding
- **Solution**: Check your API key is valid and you have API credits

**Issue**: CORS errors
- **Solution**: Access the site via `http://localhost:8000`, not by opening the HTML file directly

## License

MIT License - feel free to use for educational purposes

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/claude) for intelligent agent responses
- Designed for medical education and training purposes

---

**Disclaimer**: This is a training simulation tool and should not be used as a substitute for proper medical training or real-world surgical practice.
