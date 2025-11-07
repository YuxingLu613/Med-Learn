# Quick Start Guide

Get the Surgical Training Multi-Agent System running in 5 minutes!

## Prerequisites

- Python 3.8+
- Anthropic API key ([Get one here](https://console.anthropic.com))

## Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

### 3. Run the Application

**Option A: Using the startup script** (Linux/Mac)
```bash
chmod +x run.sh
./run.sh
```

**Option B: Directly with Python**
```bash
python backend/main.py
```

### 4. Open Your Browser

Navigate to: **http://localhost:8000**

## First Scenario

1. **Select a procedure** (e.g., "Appendectomy")
2. **Click "Start Surgery"**
3. **Select an agent** (e.g., click "👩‍⚕️ Nurse")
4. **Type a message**: "What are the patient's vital signs?"
5. **Watch the agent respond** in real-time!

## Try These Interactions

### Talk to the Anesthetist
- "Is the patient ready for anesthesia?"
- "What's the oxygen saturation?"
- "Adjust the anesthesia dosage"

### Talk to the Nurse
- "Pass me the scalpel"
- "Check the instrument count"
- "How is the bleeding?"

### Talk to the Patient (when conscious)
- "How are you feeling?"
- "Can you feel any pain?"
- "Take a deep breath"

### Talk to the Assistant
- "Help me with the retraction"
- "Prepare the sutures"
- "Check the surgical field"

## Handling Complications

When a complication appears:
1. **Read the alert** in the chat
2. **Communicate** with relevant team members
3. **Take action** based on their guidance
4. **Mark as resolved** when handled

## Advancing Through Surgery

- Use **"Advance Phase →"** button to progress
- Phases: Pre-op → Anesthesia → Incision → Procedure → Closing → Post-op
- Complete all phases to finish the surgery!

## Scoring

- **90-100**: Excellent! Expert performance
- **70-89**: Good! Solid performance
- **50-69**: Acceptable, but room for improvement
- **Below 50**: Needs more practice

## Tips for Success

1. **Communicate proactively** with all team members
2. **Handle complications immediately** when they arise
3. **Ask relevant questions** to each role
4. **Stay calm** during critical situations
5. **Think like a real surgeon** - safety first!

## Troubleshooting

**Can't connect?**
- Make sure the backend is running
- Check console for errors

**Agents not responding?**
- Verify your API key in `.env`
- Check your Anthropic API credits

**CORS errors?**
- Use `http://localhost:8000`, not file://

## Need Help?

Check the full [README.md](README.md) for detailed documentation.

---

**Happy Training! 🏥**
