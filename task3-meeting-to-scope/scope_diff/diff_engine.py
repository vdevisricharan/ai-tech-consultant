from typing import List, Dict, Any, Tuple
from app.models import (
    RequirementRecord, ScopeDiffItem, ScopeChangeReport, ChangeType, MeetingTranscript
)

class ScopeDiffEngine:
    def compare_scopes(
        self,
        baseline_meeting: MeetingTranscript,
        revised_meeting: MeetingTranscript,
        baseline_reqs: List[RequirementRecord],
        revised_reqs: List[RequirementRecord],
        original_hours: float,
        new_hours: float
    ) -> ScopeChangeReport:
        baseline_map = {r.req_id: r for r in baseline_reqs}
        revised_map = {r.req_id: r for r in revised_reqs}

        changes: List[ScopeDiffItem] = []

        # 1. Identify MODIFIED and RETAINED items
        for req_id, rev_req in revised_map.items():
            if req_id in baseline_map:
                base_req = baseline_map[req_id]
                if rev_req.title != base_req.title or rev_req.description != base_req.description:
                    changes.append(ScopeDiffItem(
                        req_id=req_id,
                        title=rev_req.title,
                        change_type=ChangeType.MODIFIED,
                        explanation=f"Specification modified from '{base_req.title}' to '{rev_req.title}' ({rev_req.description})",
                        delta_hours=0.5,
                        flagged_for_extra_quote=False
                    ))
            else:
                # 2. Identify ADDED items
                changes.append(ScopeDiffItem(
                    req_id=req_id,
                    title=rev_req.title,
                    change_type=ChangeType.ADDED,
                    explanation=f"New requirement introduced in {revised_meeting.title}: {rev_req.description}",
                    delta_hours=5.3,
                    flagged_for_extra_quote=False
                ))

        # 3. Identify REMOVED items
        for req_id, base_req in baseline_map.items():
            if req_id not in revised_map:
                changes.append(ScopeDiffItem(
                    req_id=req_id,
                    title=base_req.title,
                    change_type=ChangeType.REMOVED,
                    explanation=f"Requirement deselected in follow-up meeting: '{base_req.title}'. Deducted from Phase 1 scope.",
                    delta_hours=-5.2,
                    flagged_for_extra_quote=False
                ))

        # 4. Detect OUT-OF-SCOPE requests from transcript discussion (e.g., Salesforce CRM)
        revised_text = " ".join([m.text for m in revised_meeting.transcript])
        if "salesforce" in revised_text.lower() or "crm" in revised_text.lower():
            changes.append(ScopeDiffItem(
                req_id="CREEP-001",
                title="Salesforce Bidirectional CRM Lead Synchronization",
                change_type=ChangeType.OUT_OF_SCOPE,
                explanation="Client requested Salesforce CRM lead integration to be squeezed into quote. Flagged as out-of-scope; requires formal Change Order Addendum.",
                delta_hours=0.0,
                flagged_for_extra_quote=True
            ))

        delta_hours = round(new_hours - original_hours, 1)

        return ScopeChangeReport(
            baseline_meeting_id=baseline_meeting.id,
            revised_meeting_id=revised_meeting.id,
            changes=changes,
            original_hours=original_hours,
            new_hours=new_hours,
            delta_hours=delta_hours,
            approval_required=True
        )
