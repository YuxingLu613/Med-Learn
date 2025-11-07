"""
Scenario engine for managing surgical simulations.
Handles scenario progression, complications, and success tracking.
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class SurgeryPhase(Enum):
    """Phases of a surgical procedure."""
    PRE_OP = "pre_operative"
    ANESTHESIA = "anesthesia_induction"
    INCISION = "incision"
    PROCEDURE = "main_procedure"
    CLOSING = "closing"
    POST_OP = "post_operative"
    COMPLETED = "completed"


class ComplicationSeverity(Enum):
    """Severity levels for complications."""
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


@dataclass
class Complication:
    """Represents a surgical complication."""
    name: str
    description: str
    severity: ComplicationSeverity
    phase: SurgeryPhase
    resolved: bool = False


class SurgicalScenario:
    """Manages a surgical training scenario."""

    COMPLICATIONS = [
        Complication(
            "Unexpected Bleeding",
            "Patient is experiencing increased bleeding from the surgical site.",
            ComplicationSeverity.MODERATE,
            SurgeryPhase.PROCEDURE
        ),
        Complication(
            "Blood Pressure Drop",
            "Patient's blood pressure has dropped to 90/60.",
            ComplicationSeverity.SEVERE,
            SurgeryPhase.PROCEDURE
        ),
        Complication(
            "Allergic Reaction",
            "Patient showing signs of allergic reaction to medication.",
            ComplicationSeverity.SEVERE,
            SurgeryPhase.ANESTHESIA
        ),
        Complication(
            "Instrument Count Mismatch",
            "Surgical instrument count doesn't match pre-op count.",
            ComplicationSeverity.MODERATE,
            SurgeryPhase.CLOSING
        ),
        Complication(
            "Oxygen Saturation Drop",
            "Patient's oxygen saturation has dropped to 88%.",
            ComplicationSeverity.CRITICAL,
            SurgeryPhase.PROCEDURE
        ),
        Complication(
            "Difficult Intubation",
            "Having difficulty securing the airway.",
            ComplicationSeverity.SEVERE,
            SurgeryPhase.ANESTHESIA
        ),
    ]

    def __init__(self, procedure_name: str = "Appendectomy"):
        self.procedure_name = procedure_name
        self.current_phase = SurgeryPhase.PRE_OP
        self.active_complications: List[Complication] = []
        self.resolved_complications: List[Complication] = []
        self.actions_taken: List[str] = []
        self.messages_since_last_complication = 0
        self.complication_chance = 0.15  # 15% chance per interaction
        self.success_score = 100

    def get_current_context(self) -> str:
        """Get current scenario context for agents."""
        context = f"PROCEDURE: {self.procedure_name}\n"
        context += f"PHASE: {self.current_phase.value.replace('_', ' ').title()}\n"

        if self.active_complications:
            context += "\nACTIVE COMPLICATIONS:\n"
            for comp in self.active_complications:
                context += f"- {comp.name}: {comp.description}\n"

        return context

    def advance_phase(self):
        """Advance to the next surgical phase."""
        phases = list(SurgeryPhase)
        current_index = phases.index(self.current_phase)

        if current_index < len(phases) - 1:
            self.current_phase = phases[current_index + 1]
            return True
        return False

    def should_trigger_complication(self) -> bool:
        """Determine if a complication should occur."""
        self.messages_since_last_complication += 1

        # Increase chance over time if no complications
        adjusted_chance = self.complication_chance * (1 + self.messages_since_last_complication * 0.05)

        if random.random() < adjusted_chance:
            self.messages_since_last_complication = 0
            return True
        return False

    def trigger_complication(self) -> Optional[Complication]:
        """Trigger a random complication appropriate for current phase."""
        # Filter complications for current phase or any phase
        applicable = [
            c for c in self.COMPLICATIONS
            if c.phase == self.current_phase and c not in self.active_complications
        ]

        if applicable:
            complication = random.choice(applicable)
            self.active_complications.append(complication)
            self.success_score -= 10  # Penalty for complication occurring
            return complication

        return None

    def resolve_complication(self, complication_name: str, action: str) -> bool:
        """Resolve a complication with an action."""
        for comp in self.active_complications:
            if comp.name.lower() in complication_name.lower():
                comp.resolved = True
                self.active_complications.remove(comp)
                self.resolved_complications.append(comp)
                self.actions_taken.append(action)
                self.success_score += 5  # Bonus for resolving
                return True
        return False

    def get_status(self) -> Dict:
        """Get current scenario status."""
        return {
            "procedure": self.procedure_name,
            "phase": self.current_phase.value,
            "active_complications": [
                {"name": c.name, "description": c.description, "severity": c.severity.value}
                for c in self.active_complications
            ],
            "success_score": self.success_score,
            "is_completed": self.current_phase == SurgeryPhase.COMPLETED
        }

    def check_completion(self) -> Dict:
        """Check if surgery is complete and return results."""
        if self.current_phase == SurgeryPhase.COMPLETED:
            # Penalize for unresolved complications
            penalty = len(self.active_complications) * 20
            final_score = max(0, self.success_score - penalty)

            return {
                "completed": True,
                "success": final_score >= 50,
                "score": final_score,
                "complications_resolved": len(self.resolved_complications),
                "complications_unresolved": len(self.active_complications),
                "summary": self._generate_summary(final_score)
            }

        return {"completed": False}

    def _generate_summary(self, final_score: int) -> str:
        """Generate a summary of the surgery."""
        if final_score >= 90:
            return "Excellent performance! All complications handled expertly."
        elif final_score >= 70:
            return "Good performance. Minor issues but overall successful."
        elif final_score >= 50:
            return "Acceptable performance. Some complications remain unresolved."
        else:
            return "Poor performance. Multiple critical issues not addressed."
