from typing import List
from app.models import RequirementRecord, FeasibilityCheck, TaskEstimate, FeasibilityClassification

class EstimationAgent:
    def estimate_tasks(
        self,
        requirements: List[RequirementRecord],
        feasibility_checks: List[FeasibilityCheck]
    ) -> List[TaskEstimate]:
        feasibility_map = {f.req_id: f for f in feasibility_checks}
        estimates: List[TaskEstimate] = []

        for req in requirements:
            feas = feasibility_map.get(req.req_id)
            classification = feas.classification if feas else FeasibilityClassification.CUSTOM_DEV_REQUIRED

            if classification == FeasibilityClassification.CONFIGURABLE_OOTB:
                low, likely, high = 1.0, 2.0, 3.5
                assumptions = "Native configuration via BD Admin portal; standard QA testing."
            elif classification == FeasibilityClassification.PARTIAL_LIMITATION:
                low, likely, high = 3.0, 5.0, 8.0
                assumptions = "Native feature with custom data preparation script; schema transformation."
            else:
                if "badge" in req.title.lower():
                    low, likely, high = 3.0, 5.0, 9.0
                    assumptions = "Custom widget template override with conditional PHP logic and badge CSS."
                elif "mobile" in req.title.lower():
                    low, likely, high = 4.0, 6.0, 10.0
                    assumptions = "Responsive CSS media query adjustments across iOS Safari and Android Chrome."
                else:
                    low, likely, high = 5.0, 8.0, 14.0
                    assumptions = "Custom full-stack module development and integration."

            pert = round((low + (4 * likely) + high) / 6.0, 1)

            estimates.append(TaskEstimate(
                task_id=f"TSK-{req.req_id}",
                title=f"Implementation: {req.title}",
                deliverable=req.title,
                low_hours=low,
                likely_hours=likely,
                high_hours=high,
                pert_expected=pert,
                assumptions=assumptions,
                dependencies=["Brilliant Directories Admin Access", "Staging Environment"]
            ))

        return estimates
