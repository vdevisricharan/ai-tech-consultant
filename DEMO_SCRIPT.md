# 10-Minute Demo Video Walkthrough Script (DEMO_SCRIPT.md)

This step-by-step script follows the exact timing and rubrics specified in `Project_ AI Tech Consultant.pdf`.

---

## [0:00 – 0:30] Introduction (Camera on Face)
- **Visual**: Webcam on presenter's face.
- **Script**:
  > *"Hi everyone, I'm presenting the AI Tech Consultant. Software development pricing has crashed by 90% over the last two years—a project that used to bill for $2,000 now sells for $200. To survive and pay salaries, a tech consulting firm has to handle 10 to 20 times more clients.*
  > *Writing code is fast now; the slow part is everything around it: searching through product help articles, answering hundreds of customer emails, and turning long client meetings into scoped proposals without scope creep.*
  > *I've built one connected system across three tasks: Task 1 is our Knowledge Brain; Tasks 2 and 3 consume it exclusively over its REST API. Let's see it in action."*

---

## [0:30 – 3:00] Task 1: Knowledge Brain
- **Visual**: Screen share of Unified Console at `http://localhost:3000` on Tab 1 (Knowledge Brain).
- **Actions**:
  1. **Direct Product Question**:
     - Type: *"Can I send a mass email campaign using Brilliant Directories?"*
     - Click **Query Brain**.
     - Point out: Grounded answer generated, confidence score (92%), latency (~12ms), and clickable markdown source citation `[Can I Send A Mass Email Campaign...](URL)`.
  2. **Multimodal Screenshot Understanding**:
     - Type: *"Where is the social media tab in general settings?"*
     - Show: The answer references the exact navigation hierarchy and UI button labels extracted by Claude 3.5 Sonnet from help center screenshots.
  3. **Safe Abstention on Insufficient Evidence**:
     - Click quick button: *"How do I bake chocolate chip cookies?"*
     - Show: Status changes to `INSUFFICIENT_EVIDENCE`, confidence is 0%, and zero fake answers are hallucinated.
  4. **Human Escalation Memory Loop**:
     - Scroll to the Escalation Panel on the right.
     - Show: The unanswerable question created an escalation task. Enter an expert answer and click **Ingest Expert Resolution into Memory**. Explain how it immediately becomes retrievable for future queries.

---

## [3:00 – 5:00] Task 2: Inbox Agent
- **Visual**: Switch to Tab 2 (Inbox Agent).
- **Actions**:
  1. **Incoming Email Triage**:
     - Point out the 50 realistic emails in the left queue.
     - Select `EM-001` (How-to: custom domain DNS).
     - Show: Classified as `HOW_TO`, `SAFE`. Retrieved Task 1 evidence displayed. Generated professional reply with official documentation links.
     - Click **Approve & Send (1-Click)**.
  2. **Commercial Risk Guardrails (Refunds)**:
     - Select `EM-029` (Refund request: *"Please cancel my subscription and refund $1,450"*).
     - Point out: Classified as `REFUND_OR_CANCELLATION` with `POLICY_FINANCIAL_RISK`.
     - Highlight: The AI draft explicitly says *"our billing supervisor is reviewing your account"* and does NOT promise money. Note the warning: *"Human Approval Required"*.
  3. **20-Approval Autonomy Engine & Instant Revocation**:
     - Point to the Autonomy Status bar at the top showing the streak.
     - Explain the rule: 20 consecutive unedited approvals unlock autonomous sending for low-risk How-To emails.
     - Demonstrate rollback: Click **Edit & Send** on a draft. Show that editing draft #21 immediately resets the streak to 0 and revokes autonomy to protect the business.

---

## [5:00 – 7:45] Task 3: Meeting-to-Scope
- **Visual**: Switch to Tab 3 (Meeting to Scope).
- **Actions**:
  1. **Discovery Analysis (Meeting A)**:
     - Select `Meeting A: Apex Directory - Initial Discovery`.
     - Point out the 5-agent team execution:
       - **Requirements Table**: Extracted requirements (REQ-001 radius search, REQ-002 category hierarchy) with speaker quotes and timestamps.
       - **Feasibility Finding**: Point to the blue badge showing `CONFIGURABLE_OOTB`. Explain: *"Because our Feasibility Agent queried Task 1's API, it discovered that Brilliant Directories already supports radius search and categories out of the box, saving the client 22 hours of custom coding!"*
       - **WBS Estimates**: 3-point PERT calculation showing likely hours and total investment ($125/hr).
  2. **Scope Diff & Scope Creep Detection (Meeting C)**:
     - Click **Compare Scope Diff (C vs A)**.
     - Show the **Scope Change Report**:
       - `MODIFIED`: REQ-001 changed to support both miles and km for Canada.
       - `REMOVED`: REQ-003 (verified badge overlay) dropped to reduce budget, deducting 5.2 hours.
       - `ADDED`: REQ-006 (multi-category bulk CSV import) added.
       - `OUT_OF_SCOPE (CREEP)`: Highlight the purple badge for Salesforce CRM sync: *"The client tried to squeeze in a Salesforce integration. Our agent caught it, flagged it as out-of-scope, and required an extra change order quote!"*
  3. **Sign-Off**:
     - Click **Sign-Off & Approve Proposal** to lock the deliverable.

---

## [7:45 – 9:00] Empirical Evidence & Model Comparisons
- **Visual**: Open terminal / `evals/results.json` and display `EVALS.md`.
- **Script**:
  > *"We didn't just build features; we rigorously measured them across 60 test cases. Our overall accuracy is 88.3%, with Task 3 scoring 100% and an average query cost of $0.0023 (~20 paise).*
  > *We compared Claude 3.5 Sonnet against Claude 3.5 Haiku: Sonnet was chosen for screenshot vision and transcript diffing because it achieved zero hallucinations and caught subtle scope creep. Haiku was chosen for email classification because it was 3x faster and 75% cheaper while retaining 100% risk detection.*
  > *Now for an authentic failure case: initially, when an email asked 'How do members cancel their subscriptions themselves?', our keyword classifier saw the word 'cancel' and wrongly tagged it as a high-risk refund request. We resolved this by adding interrogative intent disambiguation."*

---

## [9:00 – 10:00] Limitations & Next Steps
- **Visual**: Return to console dashboard.
- **Script**:
  > *"In summary, the system is fully operational and runs with a single command. Its current limitations include handling CAPTCHA-protected help centers and complex real-time audio crosstalk in meetings.*
  > *Next steps would include native Gmail API webhooks and a client-facing Stripe checkout portal for signing proposals.*
  > *Thank you, and I look forward to your questions during the live review!"*
