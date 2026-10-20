import { describe, it, expect, beforeEach } from "vitest";
import { InboxAgent } from "../src/agent.js";
import { CustomerEmail } from "../src/types.js";
import fs from "fs";
import path from "path";

describe("Task 2: Inbox Agent Test Suite", () => {
  let agent: InboxAgent;
  const testStorageDir = "data/test_feedback";

  beforeEach(() => {
    // Clean test storage
    if (fs.existsSync(testStorageDir)) {
      fs.rmSync(testStorageDir, { recursive: true, force: true });
    }
    agent = new InboxAgent({
      knowledgeBrainUrl: "http://localhost:8000",
      storageDir: testStorageDir
    });
  });

  it("should classify how-to and troubleshooting emails correctly", async () => {
    const howToEmail: CustomerEmail = {
      id: "TEST-01",
      sender: "client@example.com",
      subject: "How do I configure custom domain DNS records?",
      body: "Could you provide instructions on setting up A records for my domain?"
    };

    const result = await agent.processEmail(howToEmail);
    expect(result.classification.category).toBe("HOW_TO");
    expect(result.classification.risk).toBe("SAFE");
    expect(result.draft.suggestedReply).toContain("Technical");
  });

  it("should enforce strict guardrail on refund requests (never promise unapproved refunds)", async () => {
    const refundEmail: CustomerEmail = {
      id: "TEST-02",
      sender: "unhappy@example.com",
      subject: "Cancel account and refund $1,200 immediately",
      body: "I want to cancel my subscription and get a full refund right now."
    };

    const result = await agent.processEmail(refundEmail);
    expect(result.classification.category).toBe("REFUND_OR_CANCELLATION");
    expect(result.classification.risk).toBe("POLICY_FINANCIAL_RISK");
    expect(result.draft.needsHumanApproval).toBe(true);
    expect(result.canAutoSend).toBe(false);
    expect(result.draft.suggestedReply).not.toContain("Here is your refund");
    expect(result.draft.suggestedReply).toContain("billing supervisor is reviewing");
  });

  it("should enforce commercial risk guardrail on quote requests", async () => {
    const quoteEmail: CustomerEmail = {
      id: "TEST-03",
      sender: "buyer@example.com",
      subject: "Quote request for custom iOS mobile app",
      body: "How much would you charge to build a native iOS app for our directory?"
    };

    const result = await agent.processEmail(quoteEmail);
    expect(result.classification.category).toBe("QUOTE_REQUEST");
    expect(result.classification.risk).toBe("COMMERCIAL_RISK");
    expect(result.draft.needsHumanApproval).toBe(true);
    expect(result.canAutoSend).toBe(false);
    expect(result.draft.suggestedReply).toContain("scoping discussion");
  });

  it("should implement the 20-consecutive-approval rule with rollback on edit", () => {
    const category = "HOW_TO";
    const draftText = "Standard verified instructions for domain setup.";

    // 1 to 19 unedited approvals
    for (let i = 1; i <= 19; i++) {
      const { status } = agent.submitHumanReview(
        `EM-${i}`,
        category,
        draftText,
        draftText,
        "APPROVE"
      );
      expect(status.consecutiveUneditedCount).toBe(i);
      expect(status.isAutonomous).toBe(false);
    }

    // 20th unedited approval triggers autonomy qualification
    const { status: status20 } = agent.submitHumanReview(
      "EM-20",
      category,
      draftText,
      draftText,
      "APPROVE"
    );
    expect(status20.consecutiveUneditedCount).toBe(20);
    expect(status20.isAutonomous).toBe(true);

    // 21st draft is modified by reviewer -> IMMEDIATE REVOCATION of autonomy
    const modifiedText = "Standard verified instructions for domain setup with custom notes.";
    const { status: status21 } = agent.submitHumanReview(
      "EM-21",
      category,
      draftText,
      modifiedText,
      "EDIT_AND_SEND"
    );
    expect(status21.consecutiveUneditedCount).toBe(0);
    expect(status21.isAutonomous).toBe(false);
    expect(status21.lastResetReason).toContain("Draft modified by reviewer");
  });

  it("should never grant autonomy to high-risk categories (refunds/complaints)", () => {
    const category = "REFUND_OR_CANCELLATION";
    const draftText = "We are reviewing your refund request.";

    // Attempt 25 approvals on refund category
    for (let i = 1; i <= 25; i++) {
      agent.submitHumanReview(`REF-${i}`, category, draftText, draftText, "APPROVE");
    }

    const finalStatus = agent.learningEngine.getAutonomyStatus(category);
    // Even after 25 approvals, refunds MUST NOT become autonomous
    expect(finalStatus.isAutonomous).toBe(false);
  });
});
