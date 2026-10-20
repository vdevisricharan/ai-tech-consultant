from typing import List
from app.models import RequirementRecord, ScopeOfWork, MeetingTranscript

class ScopeAgent:
    def generate_scope_of_work(
        self,
        transcript: MeetingTranscript,
        requirements: List[RequirementRecord]
    ) -> ScopeOfWork:
        deliverables = [r.title for r in requirements]
        
        exclusions = [
            "Online marketplace booking calendar with split payments (deferred to Phase 2)",
            "Third-party CRM bidirectional sync (e.g., Salesforce, HubSpot)",
            "Native mobile application store packaging (iOS / Android IPA/APK builds)",
            "Legal licensing data scraping from state government boards"
        ]

        acceptance_criteria = [
            f"Verified functional deployment of {r.title} matching agreed technical specifications."
            for r in requirements
        ]

        return ScopeOfWork(
            project_objective=f"Modernize and optimize {transcript.project_name} to improve search discovery, user experience, and platform scalability.",
            current_problem="Visitors experience inadequate location search resolution and mobile layout friction, limiting member engagement.",
            agreed_requirements=requirements,
            proposed_solution="Leverage native Brilliant Directories platform settings where feasible (saving development budget), complemented by custom widget styling and responsive CSS overrides.",
            deliverables=deliverables,
            explicit_exclusions=exclusions,
            assumptions_and_dependencies=[
                "Client provides timely access to Brilliant Directories administrator portal.",
                "Google Maps API keys are activated with Geocoding and Places APIs enabled.",
                "Client validates category tax maps and business rules prior to launch."
            ],
            acceptance_criteria=acceptance_criteria,
            client_responsibilities=[
                "Provide branding assets, color codes, and high-resolution logos.",
                "Review and sign off on staging environment within 3 business days of deployment."
            ],
            open_questions_and_risks=[
                "Risk: Google Maps API billing threshold exceeded during high traffic spikes.",
                "Question: Confirmation of whether mileage or metric units should be the primary default."
            ]
        )
