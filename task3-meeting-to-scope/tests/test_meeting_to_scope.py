import sys
import json
from pathlib import Path

# Add task3 directory to sys.path
task3_dir = Path(__file__).parent.parent
sys.path.insert(0, str(task3_dir))

import pytest
import asyncio
from app.models import (
    MeetingTranscript, ChangeType, FeasibilityClassification
)
from agents.transcript_analyst import TranscriptAnalyst
from agents.feasibility_agent import ProductFeasibilityAgent
from agents.scope_agent import ScopeAgent
from agents.estimation_agent import EstimationAgent
from agents.proposal_agent import ProposalAgent
from scope_diff.diff_engine import ScopeDiffEngine

def load_test_transcript(name: str) -> MeetingTranscript:
    fpath = task3_dir / "transcripts" / f"{name}.json"
    with open(fpath, "r", encoding="utf-8") as f:
        return MeetingTranscript(**json.load(f))

def test_transcript_analyst_extraction():
    analyst = TranscriptAnalyst(api_key="")
    t_a = load_test_transcript("transcript_a")
    reqs_a = asyncio.run(analyst.extract_requirements(t_a))

    assert len(reqs_a) == 4
    req_ids = [r.req_id for r in reqs_a]
    assert "REQ-001" in req_ids
    assert "REQ-002" in req_ids
    assert "REQ-003" in req_ids
    assert "REQ-004" in req_ids

    radius_req = [r for r in reqs_a if r.req_id == "REQ-001"][0]
    assert radius_req.speaker == "Jordan Rivera"
    assert "25-mile radius" in radius_req.raw_quote

def test_feasibility_agent_ootb_detection():
    feas_agent = ProductFeasibilityAgent()
    t_a = load_test_transcript("transcript_a")
    analyst = TranscriptAnalyst(api_key="")
    reqs_a = asyncio.run(analyst.extract_requirements(t_a))

    checks = asyncio.run(feas_agent.evaluate_all(reqs_a))
    assert len(checks) == 4
    checks_map = {c.req_id: c for c in checks}

    # REQ-001 (Radius Search) should be CONFIGURABLE_OOTB
    assert checks_map["REQ-001"].classification == FeasibilityClassification.CONFIGURABLE_OOTB
    assert checks_map["REQ-001"].hours_saved_by_ootb > 0

    # REQ-002 (Category Hierarchy) should be CONFIGURABLE_OOTB
    assert checks_map["REQ-002"].classification == FeasibilityClassification.CONFIGURABLE_OOTB
    assert checks_map["REQ-002"].hours_saved_by_ootb > 0

    # REQ-003 (Badge Overlay) should be CUSTOM_DEV_REQUIRED
    assert checks_map["REQ-003"].classification == FeasibilityClassification.CUSTOM_DEV_REQUIRED

def test_scope_and_estimation_agents():
    analyst = TranscriptAnalyst(api_key="")
    feas_agent = ProductFeasibilityAgent()
    scope_agent = ScopeAgent()
    est_agent = EstimationAgent()
    prop_agent = ProposalAgent()

    t_a = load_test_transcript("transcript_a")
    reqs_a = asyncio.run(analyst.extract_requirements(t_a))
    checks_a = asyncio.run(feas_agent.evaluate_all(reqs_a))

    # Scope of work
    sow = scope_agent.generate_scope_of_work(t_a, reqs_a)
    assert len(sow.deliverables) == 4
    assert any("booking calendar" in exc.lower() for exc in sow.explicit_exclusions)

    # Estimates
    estimates = est_agent.estimate_tasks(reqs_a, checks_a)
    assert len(estimates) == 4
    for est in estimates:
        # Check PERT formula: (low + 4*likely + high) / 6
        expected_pert = round((est.low_hours + (4 * est.likely_hours) + est.high_hours) / 6.0, 1)
        assert est.pert_expected == expected_pert

    # Proposal
    proposal = prop_agent.compile_proposal(t_a, sow, checks_a, estimates, hourly_rate=125.0)
    assert proposal.total_hours > 0
    assert proposal.total_estimated_cost_usd == round(proposal.total_hours * 125.0, 2)
    assert proposal.approval_status == "PENDING_APPROVAL"

def test_scope_diff_engine_creep_detection():
    analyst = TranscriptAnalyst(api_key="")
    feas_agent = ProductFeasibilityAgent()
    est_agent = EstimationAgent()
    diff_engine = ScopeDiffEngine()

    t_a = load_test_transcript("transcript_a")
    t_c = load_test_transcript("transcript_c")

    reqs_a = asyncio.run(analyst.extract_requirements(t_a))
    checks_a = asyncio.run(feas_agent.evaluate_all(reqs_a))
    est_a = est_agent.estimate_tasks(reqs_a, checks_a)
    hours_a = round(sum(e.pert_expected for e in est_a), 1)

    reqs_c = asyncio.run(analyst.extract_requirements(t_c))
    checks_c = asyncio.run(feas_agent.evaluate_all(reqs_c))
    est_c = est_agent.estimate_tasks(reqs_c, checks_c)
    hours_c = round(sum(e.pert_expected for e in est_c), 1)

    report = diff_engine.compare_scopes(
        baseline_meeting=t_a,
        revised_meeting=t_c,
        baseline_reqs=reqs_a,
        revised_reqs=reqs_c,
        original_hours=hours_a,
        new_hours=hours_c
    )

    change_types = [c.change_type for c in report.changes]
    assert ChangeType.MODIFIED in change_types
    assert ChangeType.REMOVED in change_types
    assert ChangeType.ADDED in change_types
    assert ChangeType.OUT_OF_SCOPE in change_types

    # REQ-001 was modified for miles & km
    mod_item = [c for c in report.changes if c.req_id == "REQ-001"][0]
    assert mod_item.change_type == ChangeType.MODIFIED

    # REQ-003 was removed to cut costs
    rem_item = [c for c in report.changes if c.req_id == "REQ-003"][0]
    assert rem_item.change_type == ChangeType.REMOVED
    assert rem_item.delta_hours < 0

    # REQ-006 was added (CSV multi-category)
    add_item = [c for c in report.changes if c.req_id == "REQ-006"][0]
    assert add_item.change_type == ChangeType.ADDED

    # Salesforce CRM was detected and flagged as out-of-scope creep requiring an extra quote
    creep_item = [c for c in report.changes if c.change_type == ChangeType.OUT_OF_SCOPE][0]
    assert "Salesforce" in creep_item.title
    assert creep_item.flagged_for_extra_quote is True
    assert report.approval_required is True
