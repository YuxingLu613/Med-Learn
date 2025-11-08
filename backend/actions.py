"""
Action system for surgical training - structured commands for each role.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class Action:
    """Represents an action that can be taken."""
    id: str
    label: str
    description: str
    target_role: str  # Which agent this action is directed to


# Define available actions for each role
NURSE_ACTIONS = [
    Action("nurse_vitals", "Check Vital Signs", "Ask nurse to report current vital signs", "nurse"),
    Action("nurse_instruments", "Request Instrument", "Ask for specific surgical instrument", "nurse"),
    Action("nurse_count", "Verify Count", "Request instrument count verification", "nurse"),
    Action("nurse_bleeding", "Assess Bleeding", "Ask nurse to assess bleeding at surgical site", "nurse"),
    Action("nurse_suction", "Increase Suction", "Request more suction", "nurse"),
    Action("nurse_sponge", "Apply Pressure", "Ask nurse to apply pressure/sponge to bleeding area", "nurse"),
]

ANESTHETIST_ACTIONS = [
    Action("anes_status", "Patient Status", "Ask for overall patient status", "anesthetist"),
    Action("anes_vitals", "Vital Signs Check", "Request detailed vital signs", "anesthetist"),
    Action("anes_oxygen", "Increase O₂", "Request increase in oxygen delivery", "anesthetist"),
    Action("anes_bp_med", "BP Medication", "Administer medication for blood pressure", "anesthetist"),
    Action("anes_fluid", "IV Fluids", "Increase IV fluid rate", "anesthetist"),
    Action("anes_depth", "Adjust Anesthesia", "Deepen or lighten anesthesia level", "anesthetist"),
    Action("anes_airway", "Check Airway", "Verify airway is secure and clear", "anesthetist"),
]

PATIENT_ACTIONS = [
    Action("patient_conscious", "Check Consciousness", "Assess patient consciousness level", "patient"),
    Action("patient_pain", "Pain Assessment", "Ask about pain level (if conscious)", "patient"),
    Action("patient_comfort", "Provide Reassurance", "Reassure and comfort the patient", "patient"),
    Action("patient_position", "Check Position", "Verify patient positioning", "patient"),
]

ASSISTANT_ACTIONS = [
    Action("assist_retract", "Retraction", "Request retraction at surgical site", "assistant"),
    Action("assist_suture", "Prepare Suture", "Ask assistant to prepare suture material", "assistant"),
    Action("assist_cautery", "Cauterize Vessel", "Request cauterization of bleeding vessel", "assistant"),
    Action("assist_field", "Clear Field", "Ask to clear and improve visibility of surgical field", "assistant"),
    Action("assist_specimen", "Handle Specimen", "Request specimen handling", "assistant"),
    Action("assist_close", "Begin Closure", "Start closing the incision", "assistant"),
]

# Map role names to their actions
ROLE_ACTIONS: Dict[str, List[Action]] = {
    "nurse": NURSE_ACTIONS,
    "anesthetist": ANESTHETIST_ACTIONS,
    "patient": PATIENT_ACTIONS,
    "assistant": ASSISTANT_ACTIONS,
}


def get_actions_for_role(role: str) -> List[Dict]:
    """Get available actions for a specific role."""
    actions = ROLE_ACTIONS.get(role, [])
    return [
        {
            "id": action.id,
            "label": action.label,
            "description": action.description
        }
        for action in actions
    ]


def get_action_prompt(action_id: str) -> str:
    """Convert action ID to a natural language prompt for the agent."""
    # Find the action across all roles
    for actions in ROLE_ACTIONS.values():
        for action in actions:
            if action.id == action_id:
                return action.description

    return "Please respond to the surgeon's request."
