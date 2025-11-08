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
    triggered_at_interaction: int = 0  # Track when it was triggered


class SurgicalScenario:
    """Manages a surgical training scenario."""

    COMPLICATIONS = [
        # Pre-operative complications
        Complication(
            "Patient Anxiety",
            "Patient showing signs of severe anxiety and elevated heart rate.",
            ComplicationSeverity.MINOR,
            SurgeryPhase.PRE_OP
        ),
        Complication(
            "Missing Lab Results",
            "Critical lab results are not available yet.",
            ComplicationSeverity.MODERATE,
            SurgeryPhase.PRE_OP
        ),
        # Anesthesia complications
        Complication(
            "Difficult Intubation",
            "Having difficulty securing the airway. Multiple attempts needed.",
            ComplicationSeverity.SEVERE,
            SurgeryPhase.ANESTHESIA
        ),
        Complication(
            "Allergic Reaction to Anesthesia",
            "Patient showing signs of allergic reaction - rash developing.",
            ComplicationSeverity.SEVERE,
            SurgeryPhase.ANESTHESIA
        ),
        Complication(
            "Blood Pressure Spike",
            "Patient's blood pressure suddenly increased to 180/110.",
            ComplicationSeverity.MODERATE,
            SurgeryPhase.ANESTHESIA
        ),
        # Incision phase
        Complication(
            "Excessive Subcutaneous Bleeding",
            "More bleeding than expected during incision.",
            ComplicationSeverity.MINOR,
            SurgeryPhase.INCISION
        ),
        Complication(
            "Adhesions Found",
            "Unexpected adhesions from previous surgery detected.",
            ComplicationSeverity.MODERATE,
            SurgeryPhase.INCISION
        ),
        # Main procedure complications
        Complication(
            "Unexpected Bleeding",
            "Significant bleeding from surgical site - vessel needs cauterization.",
            ComplicationSeverity.MODERATE,
            SurgeryPhase.PROCEDURE
        ),
        Complication(
            "Blood Pressure Drop",
            "Patient's blood pressure has dropped to 85/55 - critically low.",
            ComplicationSeverity.SEVERE,
            SurgeryPhase.PROCEDURE
        ),
        Complication(
            "Oxygen Saturation Drop",
            "Patient's oxygen saturation has dropped to 88%.",
            ComplicationSeverity.CRITICAL,
            SurgeryPhase.PROCEDURE
        ),
        Complication(
            "Arrhythmia Detected",
            "EKG showing irregular heart rhythm - possible cardiac event.",
            ComplicationSeverity.CRITICAL,
            SurgeryPhase.PROCEDURE
        ),
        Complication(
            "Anatomical Variation",
            "Encountered unexpected anatomical variation.",
            ComplicationSeverity.MODERATE,
            SurgeryPhase.PROCEDURE
        ),
        Complication(
            "Equipment Malfunction",
            "Surgical equipment is malfunctioning - need backup.",
            ComplicationSeverity.MODERATE,
            SurgeryPhase.PROCEDURE
        ),
        # Closing phase
        Complication(
            "Instrument Count Mismatch",
            "Surgical instrument count doesn't match pre-op count!",
            ComplicationSeverity.MODERATE,
            SurgeryPhase.CLOSING
        ),
        Complication(
            "Suture Line Bleeding",
            "Bleeding from suture line detected.",
            ComplicationSeverity.MINOR,
            SurgeryPhase.CLOSING
        ),
        # Post-op
        Complication(
            "Delayed Emergence",
            "Patient not waking up as expected from anesthesia.",
            ComplicationSeverity.MODERATE,
            SurgeryPhase.POST_OP
        ),
        Complication(
            "Post-op Nausea",
            "Patient experiencing severe nausea and vomiting.",
            ComplicationSeverity.MINOR,
            SurgeryPhase.POST_OP
        ),
    ]

    def __init__(self, procedure_name: str = "Appendectomy"):
        self.procedure_name = procedure_name
        self.current_phase = SurgeryPhase.PRE_OP
        self.active_complications: List[Complication] = []
        self.resolved_complications: List[Complication] = []
        self.actions_taken: List[str] = []
        self.messages_since_last_complication = 0
        self.complication_chance = 0.25  # 25% chance per interaction
        self.success_score = 100
        self.interactions_count = 0
        self.failed = False
        self.failure_reason = None
        self.patient_status = "Stable"  # Current patient condition

    def get_patient_status_description(self) -> str:
        """Generate a description of current patient status."""
        if self.failed:
            return "Critical - Surgery Failed"

        # Base status on complications and score
        critical_comps = [c for c in self.active_complications
                         if c.severity == ComplicationSeverity.CRITICAL]
        severe_comps = [c for c in self.active_complications
                       if c.severity == ComplicationSeverity.SEVERE]

        if critical_comps:
            status = f"CRITICAL - {critical_comps[0].name} requires immediate attention!"
        elif severe_comps:
            status = f"Unstable - {severe_comps[0].name} needs urgent care"
        elif len(self.active_complications) >= 2:
            status = "Moderately Unstable - Multiple complications active"
        elif len(self.active_complications) == 1:
            status = f"Fair - Managing {self.active_complications[0].name}"
        elif self.success_score >= 90:
            status = "Stable - Procedure progressing well"
        elif self.success_score >= 70:
            status = "Stable - Minor issues managed"
        else:
            status = "Guarded - Multiple issues encountered"

        return status

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
        self.interactions_count += 1

        # Increase chance over time if no complications - makes it more likely
        adjusted_chance = self.complication_chance * (1 + self.messages_since_last_complication * 0.08)

        # Guaranteed complication every 5-7 interactions if none occurred
        if self.messages_since_last_complication >= random.randint(5, 7):
            self.messages_since_last_complication = 0
            return True

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
            complication.triggered_at_interaction = self.interactions_count
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

    def check_failure(self) -> Optional[str]:
        """Check if surgery has failed due to critical mistakes.

        Returns failure reason if failed, None otherwise.
        """
        if self.failed:
            return self.failure_reason

        # Check for critical complications unresolved for too long
        for comp in self.active_complications:
            interactions_since_triggered = self.interactions_count - comp.triggered_at_interaction

            # Critical complications must be addressed within 3 interactions
            if comp.severity == ComplicationSeverity.CRITICAL and interactions_since_triggered > 3:
                self.failed = True
                self.failure_reason = f"Patient died: {comp.name} not addressed in time"
                self.success_score = 0
                return self.failure_reason

            # Severe complications must be addressed within 5 interactions
            if comp.severity == ComplicationSeverity.SEVERE and interactions_since_triggered > 5:
                self.failed = True
                self.failure_reason = f"Patient critical condition: {comp.name} ignored for too long"
                self.success_score = 0
                return self.failure_reason

        # Check for too many active complications (overwhelmed)
        if len(self.active_complications) >= 4:
            critical_count = sum(1 for c in self.active_complications
                               if c.severity in [ComplicationSeverity.CRITICAL, ComplicationSeverity.SEVERE])
            if critical_count >= 2:
                self.failed = True
                self.failure_reason = "Patient condition deteriorated - multiple critical complications"
                self.success_score = 0
                return self.failure_reason

        # Check for very low score during procedure
        if self.success_score <= 20 and self.current_phase in [SurgeryPhase.PROCEDURE, SurgeryPhase.CLOSING]:
            self.failed = True
            self.failure_reason = "Surgery aborted due to excessive complications"
            self.success_score = 0
            return self.failure_reason

        return None

    def get_status(self) -> Dict:
        """Get current scenario status."""
        return {
            "procedure": self.procedure_name,
            "phase": self.current_phase.value,
            "patient_status": self.get_patient_status_description(),
            "active_complications": [
                {"name": c.name, "description": c.description, "severity": c.severity.value}
                for c in self.active_complications
            ],
            "success_score": self.success_score,
            "is_completed": self.current_phase == SurgeryPhase.COMPLETED,
            "failed": self.failed,
            "failure_reason": self.failure_reason
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
