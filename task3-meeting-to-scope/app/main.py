import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.models import (
    MeetingTranscript, ClientProposal, ScopeChangeReport, RequirementRecord
)
from agents.transcript_analyst import TranscriptAnalyst
from agents.feasibility_agent import ProductFeasibilityAgent
from agents.scope_agent import ScopeAgent
from agents.estimation_agent import EstimationAgent
from agents.proposal_agent import ProposalAgent
from scope_diff.diff_engine import ScopeDiffEngine

app = FastAPI(
    title="Meeting-to-Scope Service",
    description="Multi-agent orchestrator for transcript analysis, feasibility checks, WBS estimation, and scope diffing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TRANSCRIPTS_DIR = Path("transcripts")

def load_transcript(transcript_id: str) -> MeetingTranscript:
    filepath = TRANSCRIPTS_DIR / f"{transcript_id.lower().replace('-', '_')}.json"
    if not filepath.exists():
        # Try finding by file prefix
        matches = list(TRANSCRIPTS_DIR.glob(f"*{transcript_id.lower()[-1]}*.json"))
        if matches:
            filepath = matches[0]
        else:
            raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        return MeetingTranscript(**data)

# Initialize Agent Team
analyst = TranscriptAnalyst(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
feasibility_agent = ProductFeasibilityAgent(knowledge_brain_url=os.getenv("KNOWLEDGE_BRAIN_URL", "http://localhost:8000"))
scope_agent = ScopeAgent()
estimation_agent = EstimationAgent()
proposal_agent = ProposalAgent()
diff_engine = ScopeDiffEngine()

class ApprovalRequest(BaseModel):
    proposal_id: str
    reviewer_name: str
    decision: str = "APPROVED" # APPROVED or REJECTED
    notes: Optional[str] = None

@app.get("/api/v1/scope/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Meeting-to-Scope Orchestrator",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/scope/transcripts")
async def list_transcripts():
    results = []
    for f in TRANSCRIPTS_DIR.glob("*.json"):
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
            results.append({
                "id": d["id"],
                "project_name": d["project_name"],
                "title": d["title"],
                "date": d["date"],
                "message_count": len(d["transcript"])
            })
    return results

@app.post("/api/v1/scope/analyze-transcript/{transcript_id}", response_model=ClientProposal)
async def analyze_transcript(transcript_id: str):
    transcript = load_transcript(transcript_id)

    # 1. Transcript Analyst extracts requirements
    reqs = await analyst.extract_requirements(transcript)

    # 2. Product Feasibility Agent checks Brilliant Directories docs via Task 1 API
    feasibility_checks = await feasibility_agent.evaluate_all(reqs)

    # 3. Scope Agent synthesizes formal 10-section SOW
    scope = scope_agent.generate_scope_of_work(transcript, reqs)

    # 4. Estimation Agent computes 3-point PERT WBS hours
    estimates = estimation_agent.estimate_tasks(reqs, feasibility_checks)

    # 5. Proposal Agent compiles client-ready proposal draft
    proposal = proposal_agent.compile_proposal(transcript, scope, feasibility_checks, estimates)

    return proposal

@app.post("/api/v1/scope/diff-transcripts", response_model=ScopeChangeReport)
async def diff_transcripts(baseline_id: str = "MEET-A", revised_id: str = "MEET-C"):
    t_base = load_transcript(baseline_id)
    t_rev = load_transcript(revised_id)

    # Analyze baseline
    reqs_base = await analyst.extract_requirements(t_base)
    feas_base = await feasibility_agent.evaluate_all(reqs_base)
    est_base = estimation_agent.estimate_tasks(reqs_base, feas_base)
    orig_hours = round(sum(e.pert_expected for e in est_base), 1)

    # Analyze revised
    reqs_rev = await analyst.extract_requirements(t_rev)
    feas_rev = await feasibility_agent.evaluate_all(reqs_rev)
    est_rev = estimation_agent.estimate_tasks(reqs_rev, feas_rev)
    new_hours = round(sum(e.pert_expected for e in est_rev), 1)

    # Compare scopes
    report = diff_engine.compare_scopes(
        baseline_meeting=t_base,
        revised_meeting=t_rev,
        baseline_reqs=reqs_base,
        revised_reqs=reqs_rev,
        original_hours=orig_hours,
        new_hours=new_hours
    )

    return report

@app.post("/api/v1/scope/approve")
async def approve_scope(req: ApprovalRequest):
    return {
        "proposal_id": req.proposal_id,
        "status": "APPROVED",
        "approved_by": req.reviewer_name,
        "approved_at": datetime.utcnow().isoformat(),
        "notes": req.notes,
        "client_ready": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
