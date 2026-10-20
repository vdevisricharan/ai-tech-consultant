import { CustomerEmail, ClassificationResult, DraftResponse, SourceReference } from "../types.js";
import { KnowledgeQueryResponse } from "../knowledge-client/client.js";

export class DraftGenerator {
  private apiKey: string;
  private model: string;
  public promptVersion: string = "v1.2.0";

  constructor(apiKey: string = process.env.ANTHROPIC_API_KEY || "", model: string = "claude-3-5-sonnet-20241022") {
    this.apiKey = apiKey;
    this.model = model;
  }

  async generateDraft(
    email: CustomerEmail,
    classification: ClassificationResult,
    knowledge: KnowledgeQueryResponse
  ): Promise<DraftResponse> {
    const sources: SourceReference[] = knowledge.sources.map(s => ({
      title: s.title,
      url: s.url,
      relevance: s.relevance
    }));

    // Enforce Human Approval Guardrails
    const isHighRisk = classification.risk !== "SAFE";
    const isMissingKnowledge = knowledge.status === "insufficient_evidence";
    const needsApproval = isHighRisk || isMissingKnowledge;

    // Build system instructions for company voice
    const systemPrompt = `You are an AI Tech Consultant communicating on behalf of a SaaS and web development consulting firm.
Voice Guidelines:
- Professional, empathetic, concise, and structured.
- If knowledge evidence is provided, use it accurately and cite the URLs.
- CRITICAL GUARDRAIL: Do NOT issue binding refunds, prices, or delivery dates unless authorized.
- Suggest concrete next steps.`;

    if (this.apiKey && !this.apiKey.startsWith("your_")) {
      try {
        const Anthropic = (await import("@anthropic-ai/sdk")).default;
        const client = new Anthropic({ apiKey: this.apiKey });

        const userPrompt = `Inbound Email:
From: ${email.sender}
Subject: ${email.subject}
Body: ${email.body}

Classification: ${classification.category} (${classification.urgency} urgency, ${classification.risk} risk)
Retrieved Knowledge Evidence:
${knowledge.answer}

Sources:
${sources.map(s => `- ${s.title}: ${s.url}`).join("\n")}

Generate a draft reply in structured JSON format:
{
  "summary": "1-sentence summary of customer need",
  "suggestedReply": "full professional email reply",
  "suggestedNextAction": "recommended follow-up action"
}`;

        const resp = await client.messages.create({
          model: this.model,
          max_tokens: 600,
          system: systemPrompt,
          messages: [{ role: "user", content: userPrompt }]
        });

        const raw = resp.content[0].type === "text" ? resp.content[0].text : "";
        const jsonMatch = raw.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0]);
          return {
            category: classification.category,
            summary: parsed.summary,
            suggestedReply: parsed.suggestedReply,
            sources,
            riskLevel: classification.risk,
            needsHumanApproval: needsApproval,
            suggestedNextAction: parsed.suggestedNextAction || "Review and dispatch",
            modelUsed: this.model,
            confidence: classification.confidence,
            tokenCount: (resp.usage?.input_tokens || 0) + (resp.usage?.output_tokens || 0)
          };
        }
      } catch (err: any) {
        console.warn(`[DraftGenerator] Claude drafting failed (${err.message}), using safe template`);
      }
    }

    // Deterministic policy-compliant fallback drafting
    return this.policyFallbackDraft(email, classification, knowledge, sources, needsApproval);
  }

  private policyFallbackDraft(
    email: CustomerEmail,
    classification: ClassificationResult,
    knowledge: KnowledgeQueryResponse,
    sources: SourceReference[],
    needsApproval: boolean
  ): DraftResponse {
    let reply = "";
    let action = "";
    const senderName = email.sender.split("@")[0].replace(".", " ");

    switch (classification.category) {
      case "HOW_TO":
      case "TROUBLESHOOTING":
        if (knowledge.status === "answered" && sources.length > 0) {
          reply = `Hi ${senderName},\n\nThank you for reaching out to technical support.\n\n${knowledge.answer}\n\nFor more detailed step-by-step guidance, please review our official documentation:\n${sources.map(s => `• ${s.title}: ${s.url}`).join("\n")}\n\nPlease let us know if you need any additional assistance.\n\nBest regards,\nTechnical Consulting Team`;
          action = "Send grounded technical resolution";
        } else {
          reply = `Hi ${senderName},\n\nThank you for reaching out. We have logged your inquiry and our senior technical consultant is reviewing the configuration details for your site. We will follow up with verified instructions within 4 business hours.\n\nBest regards,\nTechnical Consulting Team`;
          action = "Escalate to engineering for investigation";
        }
        break;

      case "REFUND_OR_CANCELLATION":
        reply = `Hi ${senderName},\n\nThank you for contacting customer service regarding your account.\n\nWe have received your cancellation request and our billing supervisor is reviewing the account details in accordance with our subscription policy. An account manager will confirm the status and processing within 1 business day.\n\nBest regards,\nBilling & Accounts Team`;
        action = "Route to billing manager for human verification";
        break;

      case "COMPLAINT":
        reply = `Hi ${senderName},\n\nThank you for bringing this to our attention. We sincerely apologize for the inconvenience and frustration this issue has caused.\n\nI have personally escalated this report to our engineering and leadership team to investigate the root cause immediately. We will update you as soon as we have a full resolution status.\n\nWarm regards,\nClient Services Team`;
        action = "Escalate to account executive and log incident";
        break;

      case "PROJECT_REQUEST":
      case "QUOTE_REQUEST":
        reply = `Hi ${senderName},\n\nThank you for your interest in expanding your platform capabilities.\n\nTo ensure we provide an accurate scope of work, technical architecture, and time estimate without scope creep, we would like to schedule a brief 20-minute scoping discussion with our technical architect.\n\nPlease let us know what times work best for you this week.\n\nBest regards,\nAI Tech Consulting Team`;
        action = "Schedule scoping discovery meeting";
        break;

      case "FOLLOW_UP":
        reply = `Hi ${senderName},\n\nThank you for following up. We are actively reviewing your ticket and deliverables. Our team will provide a comprehensive progress update shortly.\n\nBest regards,\nClient Support Team`;
        action = "Verify ticket status and reply";
        break;
    }

    return {
      category: classification.category,
      summary: `Inquiry regarding ${email.subject}`,
      suggestedReply: reply,
      sources,
      riskLevel: classification.risk,
      needsHumanApproval: needsApproval,
      suggestedNextAction: action,
      modelUsed: "heuristic-policy-v1",
      confidence: classification.confidence
    };
  }
}
