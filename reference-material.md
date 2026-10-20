# Business Labs - Assignment Prep Ref Material

# Step-by-Step Project Guide: AI Tech Consultant

The goal is to build a complete AI Tech Consultant that helps a software or service business handle customer questions, respond to emails, and turn client meetings into clear scopes of work, estimates, and proposals.

The guide below follows the requirements in your capstone document. It explains the business problem, system design, implementation sequence, individual tasks, testing, and submission requirements—without providing full working code or ready-made Claude/Cursor system prompts.

## 1. Understand the business problem first

Imagine a small software company that builds websites and provides SaaS products to clients.

Today, the company relies on people to perform three repetitive activities:

AI 고객 서비스 관리 솔루션 | Microsoft Dynamics 365

Problem 1 — Finding product knowledge

Customers ask how to configure features, process refunds, change settings, or resolve issues. The answers may exist in hundreds of help articles, but employees spend time finding them. Articles change, and screenshots may contain important information.

Business impact: slow responses, inconsistent answers, repeated work.

Remote Customer Support Jobs That Don’t Require Phone Calls (Chat & Email Roles)

Problem 2 — Responding to customer emails

Employees read each email, understand the request, search for facts, write a response, and remember follow-ups. They may repeatedly answer the same types of questions.

Business impact: high support costs, delayed replies, inconsistent tone.

Tech Nexus - Strategic Technology Consulting

Problem 3 — Converting meetings into projects

Clients describe vague requirements such as “make search better.” Someone must clarify requirements, check existing product capabilities, estimate development effort, define deliverables, and prepare a proposal.

Business impact: slow proposals, missed requirements, inaccurate estimates, scope creep.

### The proposed solution

Build three connected AI systems rather than three isolated chatbots.

Task 1 — Knowledge Brain

Ingests help articles and screenshots, answers questions, cites sources, and escalates unanswered questions.

Task 2 — Inbox Agent

Calls the Knowledge Brain API to draft and improve email responses.

Task 3 — Meeting to Scope

Calls the Knowledge Brain API to check feasibility, prepare estimates, and draft proposals.

One shared knowledge service; two downstream applications.

Critical architectural rule: Tasks 2 and 3 must consume Task 1 through its API. They must not duplicate Task 1's internal implementation. This makes the knowledge service reusable for other businesses.

JD4 Capstone Projects — Batch 1 - JD4B - Anthropic _ Applied AI _ Agentic AI.pdf

## 2. Plan the technology stack and project structure

The brief specifies the following languages and technical expectations.

| Component | Required language | Main technologies and concepts |
| --- | --- | --- |
| Task 1: Knowledge Brain | Python | Async processing, web scraping, RAG, embeddings, vector database, multimodal image understanding, API, scheduled jobs |
| Task 2: Inbox Agent | TypeScript | Node.js or Next.js, typed data, tool calling, structured JSON, feedback learning, human approval |
| Task 3: Meeting to Scope | Python | Multi-agent orchestration, long-context processing, structured outputs, estimation, scope comparison, approval |
| All tasks | As specified above | Claude at the center, evaluations, retries, clear UI, quality/cost/speed measurements |

The brief permits Python for Task 2 if the student does not know TypeScript, but says not to mix languages within a task. It also expects use of one AI coding assistant, such as Claude Code or Cursor, with the conversation history retained.

JD4 Capstone Projects — Batch 1 - JD4B - Anthropic _ Applied AI _ Agentic AI.pdf

### Suggested repository structure

This is a suggested organization, not a mandatory directory layout.

```

ai-tech-consultant/
├── task1-knowledge-brain/
│   ├── app/                 # API and business logic
│   ├── ingestion/           # Sitemap, crawling, parsing
│   ├── retrieval/           # Chunking, embeddings, search
│   ├── multimodal/           # Image understanding
│   ├── evaluation/          # Knowledge tests
│   └── tests/
├── task2-inbox-agent/
│   ├── src/
│   │   ├── email/            # Input and email classification
│   │   ├── knowledge-client/ # Calls Task 1 API
│   │   ├── drafting/         # Draft generation
│   │   ├── feedback/         # Human edits and learning
│   │   └── evaluation/
│   └── tests/
├── task3-meeting-to-scope/
│   ├── app/
│   ├── agents/              # Separate agent responsibilities
│   ├── transcripts/
│   ├── scope-diff/          # Compare meeting versions
│   ├── evaluation/
│   └── tests/
├── shared-docs/
├── README.md
├── DESIGN.md
├── EVALS.md
└── AI_LOG.md
```

Keep the tasks independently understandable and runnable. Use a small database-backed implementation where practical, and document the actual database and model choices you make.

## 3. Task 1 — Build the Knowledge Brain

Foundation for the entire project

The Knowledge Brain is the most important component because the Inbox Agent and Meeting-to-Scope system depend on it.

The brief names the Brilliant Directories Solution Center as the common source of knowledge. Its sitemap is:

`https://support.brilliantdirectories.com/support/sitemap.xml`

The system must process its articles, understand relevant screenshots, detect changes daily, answer questions with citations, and send unanswered questions to a human expert.

JD4 Capstone Projects — Batch 1 - JD4B - Anthropic _ Applied AI _ Agentic AI.pdf

### Step 1.1 — Define the input and output

Before coding, define what the service accepts and returns.

Input

- A question about product features, settings, billing, or troubleshooting.
- A list of source pages and associated screenshots.
- A human expert's answer to a previously unanswered question.

Output

- A grounded answer.
- The source articles supporting the answer.
- Relevant image references when applicable.
- A clear indication when the evidence is insufficient.
- An escalation task when human assistance is required.

This definition will become the basis for your API, retrieval design, and evaluation tests.

### Step 1.2 — Inspect the sitemap

A sitemap provides URLs to crawl. It is not necessarily a complete description of the help center's hierarchy or the full content of each article.

Your implementation should:

1. Download and parse the sitemap XML.
2. Extract article URLs and available metadata, such as last-modified timestamps.
3. Validate URLs and remove duplicates.
4. Record each URL in an ingestion manifest.
5. Identify new, changed, unchanged, and removed pages.
6. Save the manifest so a restart does not require beginning from scratch.

Business reasoning: You need to process hundreds of pages without repeatedly fetching every article or overloading the source server.

### Step 1.3 — Build a polite, resumable crawler

Design the ingestion process before implementing the entire crawl.

Read sitemap

Compare URLs with saved manifest

New page

Ingest

Changed page

Reprocess

Removed page

Deactivate

Fetch → parse → save progress → retry failures

Implement these safeguards:

- Rate limiting: Limit concurrent requests and introduce a configurable delay between requests.
- Retries: Retry temporary network failures and server errors with exponential backoff; do not retry permanent failures indefinitely.
- Checkpointing: Persist each page's status, attempts, and processing result.
- Idempotency: Reprocessing an unchanged article must not create duplicate chunks.
- Failure isolation: A failed page must not stop the entire ingestion job.
- Compliance: Respect the website's applicable crawling policies and access restrictions.

Start with 10–20 pages. Confirm the crawler is reliable before processing the complete sitemap.

### Step 1.4 — Extract article content and metadata

HTML pages contain more than useful information: navigation bars, advertisements, footers, and unrelated links can pollute retrieval.

Build an article parser that extracts:

- Article title and main body.
- Headings and section structure.
- Lists, tables, and procedural steps.
- Image URLs and their placement in the article.
- Source URL and article identifier.
- Last-modified information, if available.
- Content hash and ingestion timestamp.

Preserve the relationship between a screenshot and the text immediately surrounding it. An image without its parent article and context is much less useful.

Deliverable: A normalized collection of articles that can be inspected independently of the original HTML.

### Step 1.5 — Process screenshots and other images

The brief explicitly says that images may contain answers. A text-only RAG pipeline will therefore miss important evidence.

For each article:

1. Discover its relevant images.
2. Retrieve accessible images while respecting source restrictions.
3. Associate each image with its article and nearby text.
4. Use a vision-capable model to extract a concise description of visible content.
5. Record useful details such as interface labels, settings, buttons, and steps.
6. Store the image reference and description alongside the article metadata.
7. Keep the original image accessible for inspection or display when appropriate.

For example, an article may say “open the advanced settings,” while a screenshot identifies the exact setting label. Both pieces of information should be searchable.

Avoid treating generated image descriptions as unquestionable facts. If a screenshot is unclear, record uncertainty rather than inventing labels.

### Step 1.6 — Chunk the documents

Large articles cannot always be retrieved effectively as one document. Split them into meaningful sections.

Use this approach:

- Split at headings and topic boundaries first.
- Keep instructions and their prerequisites together.
- Keep table headers with their rows.
- Include limited overlap where context could otherwise be lost.
- Attach article title, URL, section heading, and image references to every chunk.

Test several chunking strategies rather than assuming a particular chunk size is optimal.

Example

An article about payment settings might contain separate sections for configuring a payment provider, troubleshooting failed transactions, and issuing refunds. Those sections should generally be independently retrievable.

### Step 1.7 — Create embeddings and a retrieval store

For each text chunk and relevant image description:

1. Generate an embedding using a selected embedding model.
2. Store the vector with the original text and metadata.
3. Use a vector index for semantic search.
4. Preserve a stable document and chunk identifier.
5. Support updating and deleting vectors when their source changes.

Possible implementation choices include a vector-capable PostgreSQL setup or a dedicated vector database. Choose one and explain why; the capstone does not mandate a specific database.

For better retrieval, compare:

- Semantic vector search.
- Keyword or full-text search.
- A hybrid of semantic and keyword retrieval.
- Optional reranking of the best candidate chunks.

Evaluate these alternatives on real questions. Do not choose based only on theoretical advantages.

### Step 1.8 — Implement the RAG question-answering pipeline

RAG stands for Retrieval-Augmented Generation. Instead of asking the model to answer solely from its pretrained knowledge, the system retrieves relevant source material and provides it as evidence.

User question

Retrieve relevant chunks and image descriptions

Rank evidence and check relevance

Claude

Generate a grounded answer or identify insufficient evidence.

Validate output and attach source citations

The answer-generation component should:

- Use retrieved evidence rather than inventing product behavior.
- Cite the relevant article URLs.
- Distinguish sourced facts from uncertainty.
- Say when the knowledge base does not contain enough information.
- Resist instructions embedded in retrieved documents that attempt to change system behavior.
- Return a consistent, documented response format.

Do not assume that a fluent answer is a correct answer. The evaluation stage must check factual support and citation quality.

### Step 1.9 — Design the Knowledge Brain API

Tasks 2 and 3 need a stable contract, not access to the Knowledge Brain's internal functions.

A possible API design is:

| Endpoint | Purpose |
| --- | --- |
| `POST /query` | Retrieve evidence and answer a question |
| `POST /ingestion/run` | Start or request an ingestion job |
| `GET /ingestion/status` | Inspect crawl and processing progress |
| `POST /escalations` | Create a human expert task |
| `POST /escalations/{id}/resolve` | Record an expert answer |
| `GET /health` | Check service health |

These are proposed endpoints; you may adjust them to suit your implementation.

For the query endpoint, define a typed request and response contract before building the client applications.

Example of the shape of a response:

```

{
  "answer": "Grounded answer goes here",
  "status": "answered",
  "sources": [
    {
      "title": "Relevant article",
      "url": "https://example.com/article",
      "relevance": 0.91
    }
  ],
  "confidence": 0.86,
  "needs_human": false
}
```

The values are illustrative, not actual evaluation results. Define what each field means, and ensure the confidence value is meaningful or omit it until you can calibrate it.

Include input validation, error responses, timeouts, authentication where appropriate, and API documentation. Test the API independently before integrating either downstream task.

### Step 1.10 — Implement human escalation and knowledge updates

When the system cannot answer a question safely:

1. Return an explicit insufficient-evidence status.
2. Save the question, relevant evidence, and reason for escalation.
3. Create a task for a human expert.
4. Allow the expert to enter an approved answer and, ideally, supporting evidence.
5. Store the answer as a separate, versioned knowledge record.
6. Make it available to retrieval after review.
7. Add the original question to the evaluation set.

Do not automatically treat every expert response as a universally valid product fact. It may be specific to one customer's situation, and it may need review or an expiration date.

### Step 1.11 — Keep the knowledge fresh every day

Create a scheduled ingestion job that checks the sitemap daily.

For each page, compare its current metadata or content hash with the stored version. Reprocess only the pages that changed, and deactivate removed pages so they cannot appear in future answers.

Also consider:

- Failed pages that need another attempt.
- Deleted or changed images.
- Re-indexing after changes to the chunking strategy.
- Rollback to an earlier version if ingestion corrupts content.
- A report showing the number of pages added, updated, removed, and failed.

Task 1 completion criteria

- [ ]  Full crawl works without overloading the source.
- [ ]  Interrupted jobs can resume.
- [ ]  Article text and image context are searchable.
- [ ]  Updates and removals are reflected correctly.
- [ ]  Answers include verifiable source citations.
- [ ]  Unsupported questions are escalated.
- [ ]  The API is documented and usable by an independent client.
- [ ]  At least 20 evaluation cases have been run.

## 4. Task 2 — Build the Inbox Agent

Business objective: Help customer support staff reply faster without sacrificing accuracy, appropriate tone, or human control.

The brief requires at least 50 realistic customer emails created by the student, covering different request types. It also describes a potential automatic-send rule: after 20 consecutive drafts of the same kind are sent without edits, that category may become eligible for autonomous sending.

JD4 Capstone Projects — Batch 1 - JD4B - Anthropic _ Applied AI _ Agentic AI.pdf

### Step 2.1 — Define the email categories

Begin by identifying the types of requests your agent should handle.

| Email category | Example | Risk |
| --- | --- | --- |
| How-to question | “How do I update my website logo?” | Low to moderate |
| Troubleshooting | “My payment integration stopped working.” | Moderate |
| Project request | “Can you add a new booking feature?” | Scope and pricing risk |
| Refund or cancellation | “Please cancel my plan and refund me.” | Financial/policy risk |
| Complaint | “Your latest update broke our site.” | Reputation risk |
| Quote request | “How much would this customization cost?” | Commercial risk |
| Follow-up | “Did you receive my previous request?” | Context and continuity risk |

Create the category list first. It will help you organize your dataset, choose routing logic, and define category-specific quality requirements.

### Step 2.2 — Build the email processing pipeline

Incoming email

Validate and classify intent, urgency and risk

Call Task 1 API for relevant product knowledge

Draft response using evidence and company tone

Validate claims, policy and response structure

Human review

Edit, approve or reject

Feedback record

Store outcome and version

### Step 2.3 — Create at least 50 realistic emails

Do not write 50 variations of the same question. Build a balanced dataset that covers the intended workflow.

One possible distribution is:

- 12 how-to questions.
- 10 troubleshooting emails.
- 6 project requests.
- 6 refund or cancellation requests.
- 6 complaints.
- 5 quote requests.
- 5 follow-ups.

This is a suggested distribution, not a required one.

For every email, create an expected classification, important facts, expected behavior, and risk level. Where possible, include the relevant knowledge article or indicate that the system should escalate because evidence is missing.

Keep some examples out of development and use them only for final testing. Otherwise, you may measure memorization instead of generalization.

### Step 2.4 — Integrate the Knowledge Brain

Implement a typed API client in TypeScript.

The client should:

1. Send the customer's question and useful context to Task 1.
2. Handle successful responses, timeouts, and API errors.
3. Preserve returned citations and uncertainty indicators.
4. Distinguish an answerable question from one requiring escalation.
5. Avoid creating a fabricated reply when the knowledge service fails.

When the customer asks a question about the product, use retrieved evidence to ground the draft. When the customer asks for a quote or a refund, do not assume that product documentation alone authorizes a financial or commercial commitment.

### Step 2.5 — Generate a professional draft

Design a structured output containing fields such as:

- Email category.
- Summary of the customer's request.
- Suggested reply.
- Evidence or source references.
- Risk level.
- Whether human approval is required.
- Suggested next action or follow-up date, when applicable.

Use a schema validator to check that the model returned the expected structure.

The writing should be clear, concise, and aligned with the company's voice. Avoid promises about refunds, delivery dates, prices, or technical changes unless the relevant facts and authorization are available.

### Step 2.6 — Build the human-review interface

A basic inbox screen is sufficient for an initial version.

It should display the original email, category, retrieved evidence, draft response, and review controls.

The reviewer should be able to:

- Approve and send a draft.
- Edit the draft and then send it.
- Reject it and write a replacement.
- Mark it as requiring expert assistance.
- Record the reason for a correction.

For a capstone, you can simulate email delivery through a controlled test environment if a real email integration would consume too much time. Clearly document what is simulated.

### Step 2.7 — Design the learning mechanism

The agent must learn from human decisions, but that does not mean automatically retraining the model after every email.

Start by storing each interaction:

| Field | Purpose |
| --- | --- |
| Original email | Preserve the input |
| Predicted category | Measure classification quality |
| Retrieved sources | Audit grounding |
| Generated draft | Establish the initial output |
| Human-edited reply | Capture correction |
| Final sent reply | Record actual behavior |
| Model and prompt version | Reproduce results |
| Approval outcome | Measure trust and quality |

Use this data to identify recurring corrections. For example, if reviewers consistently shorten a certain type of reply, you can revise a versioned drafting instruction or introduce an approved response pattern.

Test the revised version against a fixed regression dataset before deploying it. Preserve the ability to roll back.

### Step 2.8 — Implement the 20-consecutive-approval rule carefully

The brief allows a category to become eligible for autonomous sending after 20 consecutive drafts of the same kind are sent without modification. You need to define “same kind” and “without changing.”

A reasonable design is:

1. Define a stable category or subcategory.
2. Record whether the final sent text differs from the generated draft.
3. Track a consecutive count for that category.
4. Reset the count when a draft is edited, rejected, or fails quality checks.
5. Mark the category as eligible for a controlled autonomy trial after 20 qualifying cases.
6. Require additional safety conditions before enabling automatic sending.
7. Monitor quality continuously and disable autonomy if performance drops.

Do not count an email as unedited merely because the reviewer clicked approve. Compare the actual draft with the final sent content, using a documented comparison rule.

Important: The 20-email threshold is a condition described in the brief, not proof that the agent is safe. An email involving refunds, legal commitments, account security, or a serious complaint should remain subject to appropriate human review even if the category has accumulated 20 unchanged drafts.

### Step 2.9 — Add reliability and audit controls

- Prevent duplicate sends after retries.
- Record every generated and sent response.
- Protect personal information in stored emails and logs.
- Treat email text as untrusted input, not as instructions to override the agent's operating rules.
- Validate links and any proposed actions.
- Make autonomous sending configurable and reversible.
- Provide a clear failure state if the Knowledge Brain is unavailable.

Task 2 completion criteria

- [ ]  At least 50 realistic emails are available.
- [ ]  Email categories are correctly identified and tested.
- [ ]  The agent calls Task 1 instead of duplicating knowledge logic.
- [ ]  Drafts have structured output and supporting evidence.
- [ ]  Human approval, editing, and rejection work.
- [ ]  Feedback is versioned and used in measurable improvements.
- [ ]  The 20-consecutive-draft rule is implemented and auditable.
- [ ]  At least 20 evaluation cases have been run.

## 5. Task 3 — Build Meeting to Scope of Work

Business objective: Convert unstructured client discussions into a clear, technically feasible and commercially understandable proposal.

The system must generate three core deliverables: a scope of work, a task list with hour estimates, and a client-ready proposal. It must also process a follow-up meeting, show what changed, flag work outside the original scope, and require human approval before anything reaches the client.

JD4 Capstone Projects — Batch 1 - JD4B - Anthropic _ Applied AI _ Agentic AI.pdf

### Step 3.1 — Understand the difference between a transcript and a scope

Consider a client saying:

> “Our website search isn't great. We want customers to find products faster, and we'd like some filters. Maybe add AI as well.”
> 

This is not yet a development specification. It leaves several unanswered questions:

- What exactly is wrong with the current search?
- Which filters are needed?
- How many products are involved?
- Does the existing product already support the required filters?
- What does “AI search” mean to the client?
- What is the budget, deadline, and acceptance criterion?

Your agent team must convert vague statements into explicit requirements, while keeping assumptions separate from confirmed facts.

### Step 3.2 — Design the agent team

Do not create many agents merely to make the architecture look sophisticated. Each agent should have a distinct responsibility and produce a verifiable output.

1. Transcript Analyst

Extracts requirements, decisions, constraints, open questions and client commitments.

2. Product Feasibility Agent

Calls the Knowledge Brain to check existing features, settings and documented limitations.

3. Scope Agent

Defines deliverables, exclusions, dependencies and acceptance criteria.

4. Estimation Agent

Breaks work into tasks, estimates hours, and records assumptions and uncertainty.

5. Proposal and Review Agent

Combines the outputs, checks consistency and prepares a client-ready draft for human approval.

These roles can be implemented as separate modules or orchestrated model calls within one Python application. The important part is that each stage has a defined input, output, and validation step.

### Step 3.3 — Collect and prepare three meeting transcripts

The brief requires at least three role-played client meetings, including one follow-up meeting that changes the first.

JD4 Capstone Projects — Batch 1 - JD4B - Anthropic _ Applied AI _ Agentic AI.pdf

Use these scenarios as starting points:

Website Design for Small Businesses | Web Design for Small Businesses | ETA Web Design

Meeting A — Website improvements

A client wants improved search, filters, and a better mobile experience. Some requirements are vague; some may be achievable through existing settings.

Payment Gateway Selection Tips for Retail Success - Omnichannel payments at the Point Of Sale | Sensepass

Meeting B — E-commerce workflow

A client asks for checkout changes, order notifications, and a payment integration. Include external dependencies and questions about payment-provider support.

Start | Arendi

Meeting C — Follow-up and change requests

Continue Meeting A. The client adds a new requirement, removes one feature, and changes the expected delivery date. This transcript must test scope comparison.

Record or transcribe the conversations with appropriate consent. Store the original transcripts and their meeting dates. Keep the follow-up linked to the original project rather than treating it as a separate job.

### Step 3.4 — Handle long transcripts

Meeting transcripts may be too long to process reliably in a single model call.

Implement a staged approach:

1. Preserve the original transcript.
2. Split it into meaningful sections or overlapping chunks.
3. Extract requirements and decisions from each section.
4. Preserve the speaker and relevant timestamps where available.
5. Merge the extracted information into a project-level representation.
6. Resolve contradictions or mark them as questions.
7. Validate the final representation against the source transcript.

Do not rely on a summary alone for critical commercial commitments. Retain references to the original passages so a reviewer can verify important dates, prices, and scope decisions.

### Step 3.5 — Create a structured requirements document

Represent each requirement as a structured record rather than a free-form paragraph.

Suggested fields include:

| Field | Example |
| --- | --- |
| Requirement ID | REQ-001 |
| Description | Add filters to product search |
| Source | Meeting A, relevant passage |
| Status | Confirmed / unclear / disputed |
| Priority | Must-have / should-have / optional |
| Existing solution | To be checked |
| Acceptance criteria | What must work for the client to approve it |
| Dependencies | Product capability, external service, client input |
| Estimate status | Not estimated / estimated / needs review |

The values here illustrate the structure. Populate the records from actual transcripts rather than inventing requirements.

The system should also distinguish what the client explicitly requested from what the agent inferred.

### Step 3.6 — Check existing product features through Task 1

This step is a major business requirement.

Before proposing custom development, the feasibility agent should query the Knowledge Brain about relevant features, settings, integrations, and documented limitations.

For each requirement, classify the result into one of these categories:

- Existing configuration: The product already supports the need through settings.
- Existing feature with a limitation: The product supports part of the requirement.
- Potential custom development: No suitable documented capability was found.
- Needs clarification: The available evidence is insufficient to decide.

A missing search result does not prove that a feature does not exist. In that case, ask a human expert or flag the requirement for further investigation.

This can save the client money and prevent the company from estimating custom work unnecessarily.

### Step 3.7 — Generate the scope of work

The Scope Agent should produce a document with clear sections:

1. Project objective.
2. Current problem.
3. Agreed requirements.
4. Proposed solution.
5. Deliverables.
6. Explicit exclusions.
7. Assumptions and dependencies.
8. Acceptance criteria.
9. Client responsibilities.
10. Open questions and risks.

For each deliverable, define how success will be verified. “Improve search” is not an acceptance criterion; “allow customers to filter search results by the agreed product attributes” is closer, though the exact criteria still need client confirmation.

Do not silently convert uncertain statements into confirmed commitments.

### Step 3.8 — Estimate development hours

The Estimation Agent should break each deliverable into small engineering tasks.

For example, a search enhancement might require:

- Requirements clarification.
- Technical investigation.
- Backend changes.
- Frontend changes.
- Integration and error handling.
- Automated testing.
- Acceptance testing.
- Deployment and documentation.

For each task, record:

- Estimated hours.
- Reasoning or comparable work, where available.
- Assumptions.
- Dependencies.
- Uncertainty or confidence range.

Use an estimation table:

| Task | Low estimate | Likely estimate | High estimate |
| --- | --- | --- | --- |
| Requirements and technical design | 2 h | 3 h | 5 h |
| Backend implementation | 4 h | 7 h | 12 h |
| Frontend implementation | 3 h | 5 h | 8 h |
| Testing and integration | 2 h | 4 h | 7 h |

These figures are illustrative only, not validated estimates for a real project. Your application should derive estimates from the actual requirements and document why they are plausible.

Sum the task estimates, account for identified dependencies and risks, and expose uncertainty to the reviewer. Do not let an LLM invent a precise delivery commitment when the necessary information is unavailable.

### Step 3.9 — Create the client proposal

The Proposal Agent combines the scope and estimates into a readable document.

Recommended sections:

- Executive summary.
- Client problem and proposed solution.
- Scope and deliverables.
- Timeline and milestones.
- Estimated effort and pricing assumptions.
- Client responsibilities.
- Exclusions and dependencies.
- Risks and open questions.
- Approval and next steps.

The proposal must be consistent with the scope and estimate. For example, it should not promise an integration that the feasibility agent marked as unverified.

If you calculate a monetary price, make the hourly rate, currency, taxes, and pricing assumptions configurable. Do not treat the estimated hours as an automatically approved commercial quote.

### Step 3.10 — Compare the follow-up meeting with the original scope

This is one of the most important features to demonstrate.

When Meeting C arrives:

1. Link the transcript to the existing project.
2. Extract the latest requirements and decisions.
3. Compare them with the original approved requirements.
4. Match requirements using stable IDs or a documented matching strategy.
5. Identify additions, removals, modifications, and unresolved conflicts.
6. Re-estimate the affected work.
7. Flag out-of-scope requests for additional quotation.
8. Produce a revised scope and a change report.

Illustrative change report

Added

A new requirement for an additional search filter. Estimate and acceptance criteria need review.

Modified

The expected mobile search behavior has changed. Reassess the affected tasks.

Removed

A previously agreed deliverable is no longer required. Update the scope and estimate.

Potentially out of scope

A request was not included in the approved baseline. Flag it for clarification and additional quotation if applicable.

The labels above demonstrate the desired behavior; they are not findings from an actual meeting.

Important: Compare against the approved baseline, not merely the previous generated draft. Otherwise, an unapproved AI suggestion could accidentally become an agreed commitment.

### Step 3.11 — Add human approval and audit history

Before a scope or proposal is sent:

- Require a human reviewer to approve it.
- Show the original and revised versions.
- Highlight changed requirements and estimates.
- Display assumptions and unresolved questions.
- Record the reviewer, timestamp, and approved version.
- Keep a history of previous versions.
- Prevent an unapproved revision from being sent.

Task 3 completion criteria

- [ ]  Three role-played transcripts are stored.
- [ ]  One follow-up meeting updates an existing project.
- [ ]  Long transcripts are handled in stages.
- [ ]  Requirements retain links to source evidence.
- [ ]  Existing product capabilities are checked through Task 1.
- [ ]  Scope, task estimates, and proposal are generated.
- [ ]  Changes are compared against the approved baseline.
- [ ]  Out-of-scope requests are flagged.
- [ ]  Human approval is enforced.
- [ ]  At least 20 evaluation cases have been run.

## 6. Connect the three tasks into one application

After each task works independently, integrate them.

Shared Knowledge Brain API

Python · RAG · image-aware retrieval · citations · human escalations

Inbox Agent

TypeScript client → knowledge query → draft → review → feedback.

Meeting-to-Scope

Python client → knowledge query → scope → estimate → proposal → approval.

Shared operational principles

Versioned prompts · structured outputs · retries · human feedback · audit logs · evaluation datasets

### Integration sequence

1. Start Task 1 and verify its API.
2. Call the API from a small independent client to prove that documentation is sufficient.
3. Connect Task 2 and test both successful answers and unavailable-knowledge scenarios.
4. Connect Task 3 and verify that the feasibility agent uses the same API.
5. Add shared error handling, timeouts, and request identifiers.
6. Verify that a knowledge update affects both downstream applications without duplicating data.
7. Run the end-to-end demo from the user interface.

Do not integrate everything at once. Confirm each interface before adding the next dependency.

## 7. Evaluation framework — Prove that the system works

The capstone assigns 20 out of 100 points to evaluation, including quality, cost, speed, reliability, and safety. It requires at least 20 test cases per task and comparison of at least two models, with measurements for quality, cost, and speed. The brief also asks for 20–30 evaluations for each model-choice decision.

JD4 Capstone Projects — Batch 1 - JD4B - Anthropic _ Applied AI _ Agentic AI.pdf

That means testing should be planned before you finish implementation, not added at the end.

### Step 7.1 — Build a test suite for each task

Task 1 — Knowledge Brain

- Answer directly supported questions correctly.
- Answer questions requiring multiple articles.
- Find information available only in screenshots.
- Refuse to invent an answer when evidence is missing.
- Cite the correct article.
- Reflect updated and deleted articles.
- Resume after an interrupted ingestion job.
- Handle API timeouts and malformed requests.

Measure: retrieval relevance, factual correctness, citation correctness, abstention quality, ingestion reliability.

Task 2 — Inbox Agent

- Classify each email correctly.
- Draft a reply grounded in product knowledge.
- Handle missing evidence.
- Avoid unauthorized refunds and commitments.
- Identify complaints and urgent requests.
- Preserve relevant follow-up context.
- Record edits and approvals.
- Disable autonomous sending when quality deteriorates.

Measure: classification accuracy, draft quality, factual support, edit rate, approval rate, unsafe-action rate.

Task 3 — Meeting to Scope

- Extract explicit requirements.
- Identify missing information.
- Distinguish product configuration from custom development.
- Generate testable acceptance criteria.
- Produce plausible task estimates.
- Detect additions and removals in follow-up meetings.
- Flag out-of-scope work.
- Prevent unapproved proposals from being sent.

Measure: requirement coverage, extraction accuracy, estimate error, change-detection accuracy, approval compliance.

### Step 7.2 — Compare models using the same test cases

Use Claude as the central model family, as required by the brief. Compare at least two candidate models or configurations where appropriate.

For a fair comparison:

1. Freeze a representative evaluation dataset.
2. Use the same inputs and expected outcomes.
3. Keep prompts and other settings consistent where possible.
4. Record the model version and configuration.
5. Measure quality, cost, latency, and failure rate.
6. Review incorrect outputs manually.
7. Select the model based on the task's needs, not on one impressive example.

For example, a smaller or faster model may be suitable for email classification, while a more capable model may be justified for complex transcript analysis. This is a hypothesis to test, not an assumption about the outcome.

### Step 7.3 — Record metrics

| Metric | How to measure it |
| --- | --- |
| Quality | Percentage of test cases meeting defined correctness criteria |
| Retrieval quality | Whether the relevant source appears in the retrieved results |
| Citation accuracy | Whether cited sources actually support the answer |
| Latency | Time to complete the task; record median and tail latency |
| Cost | Model and other usage cost per completed task |
| Reliability | Successful completions divided by total attempts |
| Retry rate | Percentage of tasks requiring retries |
| Human edit rate | Percentage of drafts changed before sending |
| Safety | Number of unsafe actions or unsupported commitments |

For numerical estimates, compare the proposed estimate with a human-reviewed reference estimate. Do not judge an estimate solely by whether it looks reasonable.

### Step 7.4 — Create an evaluation record

A spreadsheet or CSV is sufficient for the first version.

```

task,case_id,model,expected,actual,quality,
latency_ms,cost,passed,failure_reason
knowledge,KB-001,model-A,...,...,...,...,...,...,...
inbox,IN-001,model-A,...,...,...,...,...,...,...
scope,SC-001,model-A,...,...,...,...,...,...,...
```

Replace the placeholders with actual measurements. Keep failed cases rather than removing them from the results.

Do not invent evaluation scores. If you have not run a test, mark it as pending. Report the results from your actual implementation in `EVALS.md`.

### Step 7.5 — Make prompt improvements measurable

For each meaningful prompt revision:

- Record the previous and new versions.
- State the problem the change is intended to fix.
- Run the same evaluation cases before and after the change.
- Check whether quality improved and whether regressions appeared.
- Compare cost and latency as well.
- Keep the ability to restore the previous version.

This satisfies the intent of self-improvement more convincingly than merely stating that the system learns from feedback.

## 8. User interface — Keep it simple and useful

The brief places significant weight on understandable UI/UX. You do not need to build a large commercial dashboard in four days. Build the smallest interface that demonstrates each business workflow.

Hannah: AI-Powered Knowledge Assistant | Itamih Case Study

Screen 1 — Knowledge Chat

Question input, answer, cited sources, image references, and a visible state for unanswered questions or escalations.

Mailo | AI Email Support - AI-driven email management for exceptional customer service | Shopify App Store

Screen 2 — Inbox Review

Email list, request category, generated reply, source evidence, edit controls, approval, and feedback history.

EstimMate

Screen 3 — Scope Builder

Transcript upload, extracted requirements, task estimates, proposal preview, change comparison, and approval state.

The screenshots above are visual references, not required designs. Implement the workflows using whichever UI framework fits your chosen stack.

Make failure states visible. For example, show “Knowledge service unavailable” rather than displaying an empty or misleading answer.

## 9. Four-day execution plan

The brief gives students four days to complete the project. The following schedule prioritizes working integrations and measurable outcomes over excessive features.

JD4 Capstone Projects — Batch 1 - JD4B - Anthropic _ Applied AI _ Agentic AI.pdf

Day 1 — Knowledge Brain foundation

Goal: a working, documented API

- Set up the repository, environment and database.
- Inspect the sitemap and implement a resumable crawl.
- Extract article text, metadata and image references.
- Implement chunking, embeddings and retrieval.
- Build the query endpoint and run initial tests.

Day 2 — Finish Task 1 and build Task 2

Goal: grounded answers and email drafts

- Add image understanding and daily update logic.
- Implement citations, abstention and human escalation.
- Create 50 realistic emails.
- Build the TypeScript API client, classification and draft generation.
- Add human review and feedback storage.

Day 3 — Build Task 3

Goal: scope, estimates and change tracking

- Create the three role-played meeting transcripts.
- Implement staged transcript analysis and structured requirements.
- Integrate the Knowledge Brain feasibility check.
- Generate task estimates and a proposal.
- Implement follow-up comparison and human approval.

Day 4 — Integration, evaluation and submission

Goal: reproducible demo and evidence

- Connect both downstream tasks to the Knowledge Brain API.
- Add error handling, retries, audit logs and basic UI polish.
- Run at least 20 evaluation cases per task.
- Compare models and record measured quality, cost and speed.
- Complete the documentation, demo video and final smoke tests.

### Prioritize if time becomes limited

Build a working end-to-end path before adding sophisticated extras.

1. Knowledge Brain ingestion, retrieval and API.
2. Inbox draft generation with human review.
3. Meeting transcript to scope, estimate and proposal.
4. Follow-up change comparison.
5. Evaluation records and model comparison.
6. Image-aware retrieval, daily incremental ingestion, and self-improvement refinements if not yet complete.

The final list is a prioritization order, not permission to omit mandatory requirements. In particular, do not leave the image-handling requirement, 50-email dataset, three transcripts, or evaluation requirements undocumented or unimplemented without clearly stating the limitation.

## 10. Prepare the required submission documents

The capstone specifies one GitHub repository, four supporting documents or deliverables, and a demo video. The writing should be concise, in plain English, and honest about limitations.

JD4 Capstone Projects — Batch 1 - JD4B - Anthropic _ Applied AI _ Agentic AI.pdf

| Deliverable | Required length | What to include |
| --- | --- | --- |
| `README.md` | Maximum 1 page | Project overview, prerequisites, configuration, setup, and one-command run instructions |
| `DESIGN.md` | 3–5 pages | Business problem, design choices, dropped features, architecture diagram, model choices, limitations, next steps |
| `EVALS.md` | 2–3 pages | At least 20 cases per task, model comparisons, quality, cost, speed, failures, and reliability |
| `AI_LOG.md` | Maximum 1 page | Five useful AI coding prompts and one example where you rejected AI-generated work, explaining why |
| Demo video | Maximum 10 minutes | First 30 seconds on camera, all three tasks working together, and at least one failure case |

### What to write in each document

README.md

Include the actual commands needed to configure and launch the application. A reviewer should not have to guess which service to start first, where credentials belong, or how to run the test suite.

DESIGN.md

Explain why the Knowledge Brain is a shared service, why each agent has its responsibilities, why you selected your models and storage, and which features you deliberately deferred. Include a diagram matching the implemented architecture.

EVALS.md

Show real test results, not anticipated results. Explain the evaluation method, model versions, dataset, cost calculation, latency measurements, failed cases, and changes made in response to failures.

AI_LOG.md

Record your real interactions with the coding assistant you selected. Do not fabricate prompts or claim to have rejected an answer that you did not actually evaluate.

### Repository and execution checks

- [ ]  Each task has its own folder and clearly separated implementation.
- [ ]  The whole project can be started with one documented command.
- [ ]  Configuration and secrets are handled safely.
- [ ]  Dependencies and setup instructions are documented.
- [ ]  Tests can be run reproducibly.
- [ ]  Commits reflect development over the four days.
- [ ]  The final repository contains no credentials or unnecessary private data.
- [ ]  You have retained the required AI coding assistant conversation history.

## 11. Final demo: a suggested 10-minute walkthrough

## 0:00

–0:30

Introduction

Explain the business problem, who the system serves, and why the three tasks share one knowledge service.

## 0:30

–3:00

Demonstrate Task 1

Ask a product question, show the answer and its citations, demonstrate a question the system cannot answer, and explain how article updates are handled.

## 3:00

–5:00

Demonstrate Task 2

Process an email, inspect the retrieved evidence, review the draft, edit or approve it, and show how feedback is recorded.

## 5:00

–7:45

Demonstrate Task 3

Process a transcript, show the requirements, feasibility check, estimate and proposal, then introduce the follow-up meeting and show the changes.

## 7:45

–9:00

Show evidence

Present evaluation results, model comparison, latency, cost, and one genuine failure with your mitigation.

## 9:00

–10:00

Close with limitations and next steps

Explain what works, what remains imperfect, and what you would improve next.

## 12. Understand how the project will be evaluated

The capstone's scoring rubric is:

Problem thinking and feature ideas

#### 15/100

Design, UI/UX, architecture and agents

#### 20/100

Code quality

#### 15/100

Prompt design and self-improvement

#### 15/100

Evaluation, cost, speed, reliability and safety

#### 20/100

Writing and demo

#### 15/100

According to the brief, a student needs a total score of at least 80/100 and at least 60% of the available points in every section to qualify as a fit. A high total cannot compensate for a section below its minimum. The process also includes a 30-minute live review and hidden test cases.

JD4 Capstone Projects — Batch 1 - JD4B - Anthropic _ Applied AI _ Agentic AI.pdf

That has three practical implications:

1. Build something you can explain. Be ready to explain your retrieval process, agent handoffs, API contracts, data model, and failure handling.
2. Show measurements. A small but carefully evaluated implementation is more convincing than unsupported claims about accuracy or speed.
3. Demonstrate a failure. Show what happens when the knowledge base has no answer, a dependency fails, or a client changes the scope. Explain why your system responds that way.

## 13. Final project completion checklist

Use this checklist to track implementation progress.

## Project tracker

### 0/22

Task 1 — Knowledge Brain

- [ ]  Sitemap crawler and resumable ingestion
    
- [ ]  Article parsing and image understanding
    
- [ ]  Chunking, embeddings and retrieval
    
- [ ]  Grounded answers and citations
    
- [ ]  Daily incremental updates and deletion handling
    
- [ ]  API documentation and human escalation
    

Task 2 — Inbox Agent

- [ ]  50 realistic customer emails
    
- [ ]  Classification and Knowledge Brain integration
    
- [ ]  Structured email drafts
    
- [ ]  Human review and feedback history
    
- [ ]  20-consecutive-approval logic and safeguards
    

Task 3 — Meeting to Scope

- [ ]  Three role-played meeting transcripts
    
- [ ]  Structured requirements and source references
    
- [ ]  Product feasibility checks
    
- [ ]  Scope, estimates and proposal
    
- [ ]  Follow-up change detection and human approval
    

Submission and evaluation

- [ ]  20 or more evaluation cases per task
    
- [ ]  Model comparisons with measured cost and latency
    
- [ ]  README.md, DESIGN.md, EVALS.md and AI_LOG.md
    
- [ ]  One-command project startup
    
- [ ]  Demo video including a failure case
    
- [ ]  Repository and live-review readiness