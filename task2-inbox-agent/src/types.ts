import { z } from "zod";

export const EmailCategorySchema = z.enum([
  "HOW_TO",
  "TROUBLESHOOTING",
  "PROJECT_REQUEST",
  "REFUND_OR_CANCELLATION",
  "COMPLAINT",
  "QUOTE_REQUEST",
  "FOLLOW_UP"
]);
export type EmailCategory = z.infer<typeof EmailCategorySchema>;

export const UrgencyLevelSchema = z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]);
export type UrgencyLevel = z.infer<typeof UrgencyLevelSchema>;

export const RiskLevelSchema = z.enum([
  "SAFE",
  "COMMERCIAL_RISK",
  "POLICY_FINANCIAL_RISK",
  "REPUTATIONAL_RISK"
]);
export type RiskLevel = z.infer<typeof RiskLevelSchema>;

export const CustomerEmailSchema = z.object({
  id: z.string(),
  sender: z.string().email(),
  subject: z.string(),
  body: z.string(),
  receivedAt: z.string().optional()
});
export type CustomerEmail = z.infer<typeof CustomerEmailSchema>;

export const ClassificationResultSchema = z.object({
  category: EmailCategorySchema,
  urgency: UrgencyLevelSchema,
  risk: RiskLevelSchema,
  confidence: z.number().min(0).max(1),
  reasoning: z.string()
});
export type ClassificationResult = z.infer<typeof ClassificationResultSchema>;

export const SourceReferenceSchema = z.object({
  title: z.string(),
  url: z.string(),
  relevance: z.number().optional()
});
export type SourceReference = z.infer<typeof SourceReferenceSchema>;

export const DraftResponseSchema = z.object({
  category: EmailCategorySchema,
  summary: z.string(),
  suggestedReply: z.string(),
  sources: z.array(SourceReferenceSchema),
  riskLevel: RiskLevelSchema,
  needsHumanApproval: z.boolean(),
  suggestedNextAction: z.string(),
  modelUsed: z.string(),
  confidence: z.number(),
  tokenCount: z.number().optional()
});
export type DraftResponse = z.infer<typeof DraftResponseSchema>;

export const HumanActionSchema = z.enum([
  "APPROVE",
  "EDIT_AND_SEND",
  "REJECT",
  "ESCALATE"
]);
export type HumanAction = z.infer<typeof HumanActionSchema>;

export const FeedbackRecordSchema = z.object({
  emailId: z.string(),
  category: EmailCategorySchema,
  promptVersion: string(),
  generatedDraft: z.string(),
  finalSentReply: z.string(),
  action: HumanActionSchema,
  editDiffRatio: z.number().min(0).max(1),
  reviewerNotes: z.string().optional(),
  timestamp: z.string()
});
export type FeedbackRecord = z.infer<typeof FeedbackRecordSchema>;

export const AutonomyStatusSchema = z.object({
  category: EmailCategorySchema,
  consecutiveUneditedCount: z.number(),
  isAutonomous: z.boolean(),
  totalSent: z.number(),
  lastResetReason: z.string().optional()
});
export type AutonomyStatus = z.infer<typeof AutonomyStatusSchema>;

function string() {
  return z.string();
}
