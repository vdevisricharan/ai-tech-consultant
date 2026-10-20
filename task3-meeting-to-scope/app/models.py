from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FeasibilityClassification(str, Enum):
    CONFIGURABLE_OOTB = "CONFIGURABLE_OOTB"
    PARTIAL_LIMITATION = "PARTIAL_LIMITATION"
    CUSTOM_DEV_REQUIRED = "CUSTOM_DEV_REQUIRED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"

class ChangeType(str, Enum):
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    REMOVED = "REMOVED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"

class TranscriptMessage(BaseModel):
    speaker: str
    timestamp: str
    text: str

class MeetingTranscript(BaseModel):
    id: str
    project_name: str
    title: str
    date: str
    participants: List[Dict[str, str]] = Field(default_factory=list)
    transcript: List[TranscriptMessage]

class RequirementRecord(BaseModel):
    req_id: str
    title: str
    description: str
    raw_quote: str
    speaker: str
    timestamp: str
    category: str
    priority: str = "MUST_HAVE" # MUST_HAVE, SHOULD_HAVE, OPTIONAL
    status: str = "CONFIRMED"

class FeasibilityCheck(BaseModel):
    req_id: str
    classification: FeasibilityClassification
    confidence: float
    evidence_sources: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_approach: str
    hours_saved_by_ootb: float = 0.0

class TaskEstimate(BaseModel):
    task_id: str
    title: str
    deliverable: str
    low_hours: float
    likely_hours: float
    high_hours: float
    pert_expected: float
    assumptions: str
    dependencies: List[str] = Field(default_factory=list)

class ScopeOfWork(BaseModel):
    project_objective: str
    current_problem: str
    agreed_requirements: List[RequirementRecord]
    proposed_solution: str
    deliverables: List[str]
    explicit_exclusions: List[str]
    assumptions_and_dependencies: List[str]
    acceptance_criteria: List[str]
    client_responsibilities: List[str]
    open_questions_and_risks: List[str]

class ScopeDiffItem(BaseModel):
    req_id: str
    title: str
    change_type: ChangeType
    explanation: str
    delta_hours: float
    flagged_for_extra_quote: bool = False

class ScopeChangeReport(BaseModel):
    baseline_meeting_id: str
    revised_meeting_id: str
    changes: List[ScopeDiffItem]
    original_hours: float
    new_hours: float
    delta_hours: float
    approval_required: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

class ClientProposal(BaseModel):
    project_name: str
    executive_summary: str
    scope_of_work: ScopeOfWork
    feasibility_checks: List[FeasibilityCheck]
    wbs_estimates: List[TaskEstimate]
    total_hours: float
    estimated_duration_weeks: int
    hourly_rate_usd: float = 125.0
    total_estimated_cost_usd: float
    approval_status: str = "PENDING_APPROVAL"
