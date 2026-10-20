# AI Tech Consultant

The AI Tech Consultant automates the three most expensive bottlenecks in technical software consulting: looking up domain knowledge, drafting high-volume customer emails, and turning messy client meetings into scoped proposals.

Tasks 2 and 3 call Task 1 exclusively through its REST API, ensuring zero code duplication.

---

## What It Does

1. **Task 1: Knowledge Brain (Python / FastAPI)**
   - Polite, resumable crawler that parses Brilliant Directories help articles and UI screenshots.
   - Hybrid search (SQLite FTS5 BM25 + semantic vectors) with Reciprocal Rank Fusion (RRF).
   - Grounded RAG with exact URL citations. Safely abstains (`insufficient_evidence`) when information is missing.
   - Human escalation loop: expert answers flow back into vector memory.

2. **Task 2: Inbox Agent (Strict TypeScript / Node.js)**
   - Classifies customer emails across 7 categories (how-to, troubleshooting, project, refund, complaint, quote, follow-up).
   - Generates structured replies grounded in Task 1 knowledge.
   - Enforces commercial guardrails: never promises unapproved refunds or arbitrary quotes.
   - Implements the 20-consecutive-approval rule: low-risk how-to emails unlock autonomy after 20 unedited sends; human edits revoke autonomy instantly.

3. **Task 3: Meeting-to-Scope (Python / Multi-Agent)**
   - 5 specialized agents: Transcript Analyst, Product Feasibility Agent (calls Task 1), Scope Agent, Estimation Agent, Proposal Agent.
   - Feasibility checks identify out-of-the-box settings, saving clients budget.
   - 3-point PERT work breakdown structure (WBS) estimates.
   - Scope Diff Engine detects changes across meetings (Added, Modified, Removed) and flags out-of-scope creep (e.g., Salesforce CRM sync) for extra quotation.

---

## Quickstart (One-Command Run)

### 1. Prerequisites
- Python 3.11+
- Node.js v20+

### 2. Setup (One Time)
```bash
# Clone & enter directory
git clone <repo-url>
cd ai-tech-consultant

# Create virtual environment & install Python dependencies
python -m venv .venv
.\.venv\Scripts\pip install -r task1-knowledge-brain/requirements.txt

# Install Node dependencies
cd task2-inbox-agent && npm install && cd ..
```

### 3. Launch Everything (One Command)
```powershell
.\run.ps1
# Or on any OS:
.\.venv\Scripts\python run_all.py
```

### 4. Verified Services
- **Web Console & Unified UI**: [http://localhost:3000](http://localhost:3000)
- **Task 1 Knowledge Brain API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Task 3 Meeting-to-Scope API Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## Running the Automated Test Suites & Evaluations

```bash
# Run Task 1 Unit Tests (Pytest)
.\.venv\Scripts\pytest task1-knowledge-brain/tests/test_knowledge_brain.py -v

# Run Task 2 Unit Tests (Vitest - Strict TypeScript)
cd task2-inbox-agent && npm test && cd ..

# Run Task 3 Unit Tests (Pytest)
.\.venv\Scripts\pytest task3-meeting-to-scope/tests/test_meeting_to_scope.py -v

# Run Full 60-Evaluation Benchmark Matrix (Quality, Cost & Latency)
.\.venv\Scripts\python evals/run_evals.py
```
