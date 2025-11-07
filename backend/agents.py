"""
Multi-agent system for surgical training simulation.
Each agent represents a different role in the operating room.
"""

from typing import List, Dict
import anthropic
import os
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str


class SurgicalAgent:
    """Base class for all surgical simulation agents."""

    def __init__(self, role: str, personality: str, expertise: str):
        self.role = role
        self.personality = personality
        self.expertise = expertise
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.conversation_history: List[Dict] = []

    def get_system_prompt(self, scenario_context: str) -> str:
        """Generate system prompt for the agent."""
        return f"""You are {self.role} in a surgical training simulation.

PERSONALITY: {self.personality}

EXPERTISE: {self.expertise}

CURRENT SCENARIO: {scenario_context}

Your role is to:
1. Respond realistically to the clinician's questions and instructions
2. Provide appropriate information based on your role
3. React to complications and scenario changes
4. Help or hinder based on the situation (realistically)
5. Stay in character at all times

Keep responses concise (2-3 sentences) and professional. Respond as you would in a real operating room."""

    def respond(self, user_message: str, scenario_context: str) -> str:
        """Generate a response based on user input and scenario context."""

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Generate response
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            system=self.get_system_prompt(scenario_context),
            messages=self.conversation_history
        )

        assistant_message = response.content[0].text

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def reset(self):
        """Reset conversation history."""
        self.conversation_history = []


class NurseAgent(SurgicalAgent):
    """Surgical nurse agent."""

    def __init__(self):
        super().__init__(
            role="Surgical Nurse",
            personality="Experienced, attentive, and detail-oriented. You monitor instruments and patient status closely.",
            expertise="Instrument management, sterile technique, patient monitoring, assisting with procedures"
        )


class AnesthetistAgent(SurgicalAgent):
    """Anesthetist agent."""

    def __init__(self):
        super().__init__(
            role="Anesthetist",
            personality="Calm under pressure, highly focused on vital signs and patient stability.",
            expertise="Anesthesia management, airway control, vital signs monitoring, drug administration, patient consciousness levels"
        )


class PatientAgent(SurgicalAgent):
    """Patient agent (responds based on consciousness level and condition)."""

    def __init__(self):
        super().__init__(
            role="Patient",
            personality="Anxious but trusting. Your responses depend on your consciousness level and condition.",
            expertise="Experiencing the surgery, reporting symptoms when conscious, physiological responses"
        )


class SurgicalAssistantAgent(SurgicalAgent):
    """Surgical assistant agent."""

    def __init__(self):
        super().__init__(
            role="Surgical Assistant",
            personality="Eager to help, knowledgeable but defers to the lead surgeon.",
            expertise="Assisting with procedures, maintaining surgical field, retraction, suturing"
        )


class AgentOrchestrator:
    """Manages all agents and coordinates their interactions."""

    def __init__(self):
        self.agents = {
            "nurse": NurseAgent(),
            "anesthetist": AnesthetistAgent(),
            "patient": PatientAgent(),
            "assistant": SurgicalAssistantAgent()
        }

    def get_agent(self, agent_type: str) -> SurgicalAgent:
        """Get agent by type."""
        return self.agents.get(agent_type.lower())

    def reset_all(self):
        """Reset all agents."""
        for agent in self.agents.values():
            agent.reset()

    def get_available_agents(self) -> List[str]:
        """Get list of available agent types."""
        return list(self.agents.keys())
