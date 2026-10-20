import fs from "fs";
import path from "path";
import { EmailCategory, FeedbackRecord, AutonomyStatus, HumanAction } from "../types.js";

export class FeedbackLearningEngine {
  private historyFile: string;
  private autonomyState: Map<EmailCategory, AutonomyStatus> = new Map();

  constructor(storageDir: string = "data") {
    const dir = path.resolve(storageDir);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    this.historyFile = path.join(dir, "feedback_history.json");
    this.initAutonomyState();
    this.loadHistory();
  }

  private initAutonomyState() {
    const categories: EmailCategory[] = [
      "HOW_TO",
      "TROUBLESHOOTING",
      "PROJECT_REQUEST",
      "REFUND_OR_CANCELLATION",
      "COMPLAINT",
      "QUOTE_REQUEST",
      "FOLLOW_UP"
    ];
    for (const cat of categories) {
      this.autonomyState.set(cat, {
        category: cat,
        consecutiveUneditedCount: 0,
        isAutonomous: false,
        totalSent: 0
      });
    }
  }

  private computeDiffRatio(str1: string, str2: string): number {
    const s1 = str1.trim().replace(/\s+/g, " ");
    const s2 = str2.trim().replace(/\s+/g, " ");
    if (s1 === s2) return 0.0;
    
    const words1 = s1.split(" ");
    const words2 = s2.split(" ");
    let matches = 0;
    const set2 = new Set(words2);
    for (const w of words1) {
      if (set2.has(w)) matches++;
    }
    const maxLen = Math.max(words1.length, words2.length);
    if (maxLen === 0) return 0.0;
    return Math.max(0.0, Math.min(1.0, 1.0 - (matches / maxLen)));
  }

  recordFeedback(
    emailId: string,
    category: EmailCategory,
    promptVersion: string,
    generatedDraft: string,
    finalSentReply: string,
    action: HumanAction,
    reviewerNotes?: string
  ): { status: AutonomyStatus; record: FeedbackRecord } {
    const diffRatio = this.computeDiffRatio(generatedDraft, finalSentReply);
    const status = this.autonomyState.get(category)!;
    status.totalSent += 1;

    // Evaluate 20-consecutive-approval rule
    // Safety constraint: ONLY "HOW_TO" and low-risk categories are eligible for autonomous sending
    const isEligibleCategory = category === "HOW_TO";

    if (action === "APPROVE" && diffRatio === 0.0) {
      status.consecutiveUneditedCount += 1;
      if (status.consecutiveUneditedCount >= 20 && isEligibleCategory) {
        status.isAutonomous = true;
      }
    } else {
      // Any human modification, rejection, or escalation RESETS streak to 0 and revokes autonomy
      const prevAutonomy = status.isAutonomous;
      status.consecutiveUneditedCount = 0;
      status.isAutonomous = false;
      status.lastResetReason = action === "EDIT_AND_SEND" 
        ? `Draft modified by reviewer (diff ratio: ${diffRatio.toFixed(2)})`
        : `Action was ${action}`;
      
      if (prevAutonomy) {
        console.warn(`[Autonomy Safeguard] Autonomy REVOKED for category ${category}. Reason: ${status.lastResetReason}`);
      }
    }

    const record: FeedbackRecord = {
      emailId,
      category,
      promptVersion,
      generatedDraft,
      finalSentReply,
      action,
      editDiffRatio: diffRatio,
      reviewerNotes,
      timestamp: new Date().toISOString()
    };

    this.persistRecord(record);
    return { status, record };
  }

  getAutonomyStatus(category: EmailCategory): AutonomyStatus {
    return this.autonomyState.get(category)!;
  }

  getAllAutonomyStatuses(): AutonomyStatus[] {
    return Array.from(this.autonomyState.values());
  }

  private persistRecord(record: FeedbackRecord) {
    let history: FeedbackRecord[] = [];
    if (fs.existsSync(this.historyFile)) {
      try {
        history = JSON.parse(fs.readFileSync(this.historyFile, "utf-8"));
      } catch {
        history = [];
      }
    }
    history.push(record);
    fs.writeFileSync(this.historyFile, JSON.stringify(history, null, 2), "utf-8");
  }

  private loadHistory() {
    if (fs.existsSync(this.historyFile)) {
      try {
        const history: FeedbackRecord[] = JSON.parse(fs.readFileSync(this.historyFile, "utf-8"));
        for (const rec of history) {
          const status = this.autonomyState.get(rec.category);
          if (status) {
            status.totalSent += 1;
            if (rec.action === "APPROVE" && rec.editDiffRatio === 0.0) {
              status.consecutiveUneditedCount += 1;
              if (status.consecutiveUneditedCount >= 20 && rec.category === "HOW_TO") {
                status.isAutonomous = true;
              }
            } else {
              status.consecutiveUneditedCount = 0;
              status.isAutonomous = false;
            }
          }
        }
      } catch (e) {
        console.warn("[FeedbackLearning] Could not parse existing history file:", e);
      }
    }
  }
}
