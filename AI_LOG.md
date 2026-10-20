# AI Interaction & Prompt Engineering Log (AI_LOG.md)

This log records the 5 most valuable prompts used during the development of the AI Tech Consultant, along with one critical instance where an AI suggestion was rejected with technical justification.

---

## The 5 Most Useful Prompts

### Prompt 1: Resumable Sitemap Crawler Architecture (Task 1)
> *"Design an asynchronous Python crawler for `support.brilliantdirectories.com/support/sitemap.xml`. It must maintain an SQLite manifest tracking URL, content_hash, last_scraped_at, and status (NEW, INDEXED, MODIFIED, DELETED, FAILED). Include a concurrency semaphore of 3, 350ms delay with jitter, and exponential backoff for 429/503 errors. Reprocessing an unchanged hash must be idempotent."*
- **Why it worked**: Enforced enterprise crawling safeguards, preventing IP blocks while making interrupted crawls instantly resumable.

### Prompt 2: Multimodal Image Understanding with UI Extraction (Task 1)
> *"Given an inline screenshot from a Brilliant Directories help article, prompt Claude 3.5 Sonnet to extract specific UI field names, button labels, settings toggles, and navigation breadcrumbs. Return a concise 3-sentence summary and a comma-separated list of visible interface labels. Do not invent labels if the image is blurry."*
- **Why it worked**: Transformed static image pixels into indexed semantic text chunks, enabling answers to questions like *"Where is the social media tab?"*

### Prompt 3: 20-Consecutive-Approval Autonomy Engine with Instant Rollback (Task 2)
> *"Implement the 20-consecutive-approval rule in TypeScript. Track consecutive unedited sends per category using whitespace-normalized diffing. If the streak reaches 20, mark the category eligible for autonomous sending—but ONLY for low-risk HOW_TO emails. If a human edits a draft, rejects it, or escalates, immediately reset the streak to 0 and revoke autonomy. Provide full unit tests."*
- **Why it worked**: Guaranteed commercial safety by hard-locking financial/refund emails from ever going out autonomously while building a testable, auditable state machine.

### Prompt 4: Three-Point PERT Estimation & Feasibility Verification (Task 3)
> *"Write a Python estimation agent that takes extracted meeting requirements and checks them against Task 1's API. If an out-of-the-box setting solves the need, assign 1-2 hours and log the hours saved. For custom code, break tasks into engineering subtasks and calculate Three-Point PERT hours: (Low + 4*Likely + High) / 6. Output structured TaskEstimate Pydantic models."*
- **Why it worked**: Replaced arbitrary LLM guesses with standard engineering estimation math and highlighted commercial savings for the client.

### Prompt 5: Scope Diff Engine & Scope Creep Detector (Task 3)
> *"Compare Meeting C against the approved baseline of Meeting A. Detect Added, Modified, and Removed requirements. Additionally, scan the transcript for conversational scope creep (e.g. asking to squeeze in Salesforce CRM sync) and flag them as OUT_OF_SCOPE with extra quotation required. Prevent unapproved revisions from generating final proposals."*
- **Why it worked**: Automated contract protection, catching unquoted feature creep before commitments reached the client.

---

## One Time I Rejected the AI's Answer and Why

### The AI's Proposal
During the design of the retrieval store, the AI assistant recommended setting up **Pinecone with a remote vector index**, or running **PostgreSQL with pgvector inside a multi-container Docker Compose setup**.

### Why I Rejected It
1. **Scoring Constraint**: The capstone evaluation rubric mandates: *"The whole project runs with one command."*
2. **Reviewer Friction**: Requiring an evaluator to register for third-party cloud API keys (Pinecone) or install Docker Desktop with PostgreSQL creates high setup friction and immediate failure if Docker is not configured on their machine.
3. **Overkill Complexity**: For 25 to 1,500 help articles, an external cloud vector database adds unnecessary network latency (150ms+ per query) and external points of failure.

### The Superior Alternative
I rejected external cloud vector databases and implemented an **embedded SQLite hybrid store** combining **FTS5 BM25 keyword matching** with **vector embeddings and Reciprocal Rank Fusion (RRF)**. It has zero external dependencies, boots in under 1 second, and runs entirely in local memory and disk with 100% test reproducibility.
