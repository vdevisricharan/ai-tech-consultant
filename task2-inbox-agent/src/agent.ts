import { CustomerEmail, DraftResponse, ClassificationResult, HumanAction, FeedbackRecord, AutonomyStatus } from "./types.js";
import { EmailClassifier } from "./email/classifier.js";
import { KnowledgeBrainClient } from "./knowledge-client/client.js";
import { DraftGenerator } from "./drafting/generator.js";
import { FeedbackLearningEngine } from "./feedback/learning.js";

export class InboxAgent {
  public classifier: EmailClassifier;
  public knowledgeClient: KnowledgeBrainClient;
  public generator: DraftGenerator;
  public learningEngine: FeedbackLearningEngine;

  constructor(options?: {
    apiKey?: string;
    knowledgeBrainUrl?: string;
    classifierModel?: string;
    draftingModel?: string;
    storageDir?: string;
  }) {
    this.classifier = new EmailClassifier(options?.apiKey, options?.classifierModel);
    this.knowledgeClient = new KnowledgeBrainClient(options?.knowledgeBrainUrl);
    this.generator = new DraftGenerator(options?.apiKey, options?.draftingModel);
    this.learningEngine = new FeedbackLearningEngine(options?.storageDir);
  }

  async processEmail(email: CustomerEmail): Promise<{
    email: CustomerEmail;
    classification: ClassificationResult;
    draft: DraftResponse;
    canAutoSend: boolean;
  }> {
    // 1. Classify intent and risk
    const classification = await this.classifier.classify(email);

    // 2. Query Knowledge Brain for grounded product documentation
    const queryTerm = `${email.subject} ${email.body.slice(0, 150)}`;
    const knowledge = await this.knowledgeClient.query(queryTerm);

    // 3. Generate structured draft reply
    const draft = await this.generator.generateDraft(email, classification, knowledge);

    // 4. Check autonomy status
    const autonomy = this.learningEngine.getAutonomyStatus(classification.category);
    const canAutoSend = autonomy.isAutonomous && !draft.needsHumanApproval;

    return {
      email,
      classification,
      draft,
      canAutoSend
    };
  }

  submitHumanReview(
    emailId: string,
    category: any,
    generatedDraft: string,
    finalSentReply: string,
    action: HumanAction,
    notes?: string
  ): { status: AutonomyStatus; record: FeedbackRecord } {
    return this.learningEngine.recordFeedback(
      emailId,
      category,
      this.generator.promptVersion,
      generatedDraft,
      finalSentReply,
      action,
      notes
    );
  }
}
