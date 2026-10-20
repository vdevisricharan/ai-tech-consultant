import { CustomerEmail, ClassificationResult, EmailCategory, RiskLevel, UrgencyLevel } from "../types.js";

export class EmailClassifier {
  private apiKey: string;
  private model: string;

  constructor(apiKey: string = process.env.ANTHROPIC_API_KEY || "", model: string = "claude-3-5-haiku-20241022") {
    this.apiKey = apiKey;
    this.model = model;
  }

  async classify(email: CustomerEmail): Promise<ClassificationResult> {
    // If Anthropic API Key is valid, use Claude
    if (this.apiKey && !this.apiKey.startsWith("your_")) {
      try {
        const Anthropic = (await import("@anthropic-ai/sdk")).default;
        const client = new Anthropic({ apiKey: this.apiKey });

        const prompt = `Classify this customer support email for an AI Tech Consultant:
Subject: "${email.subject}"
Body: "${email.body}"

Respond in pure JSON matching this exact schema:
{
  "category": "HOW_TO" | "TROUBLESHOOTING" | "PROJECT_REQUEST" | "REFUND_OR_CANCELLATION" | "COMPLAINT" | "QUOTE_REQUEST" | "FOLLOW_UP",
  "urgency": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "risk": "SAFE" | "COMMERCIAL_RISK" | "POLICY_FINANCIAL_RISK" | "REPUTATIONAL_RISK",
  "confidence": number between 0 and 1,
  "reasoning": "brief explanation"
}`;

        const response = await client.messages.create({
          model: this.model,
          max_tokens: 300,
          messages: [{ role: "user", content: prompt }]
        });

        const raw = response.content[0].type === "text" ? response.content[0].text : "";
        const jsonMatch = raw.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0]);
          return {
            category: parsed.category as EmailCategory,
            urgency: parsed.urgency as UrgencyLevel,
            risk: parsed.risk as RiskLevel,
            confidence: Number(parsed.confidence) || 0.9,
            reasoning: parsed.reasoning || "Classified via Claude Haiku"
          };
        }
      } catch (err: any) {
        console.warn(`[EmailClassifier] Claude classification failed (${err.message}), using heuristic fallback`);
      }
    }

    // Deterministic semantic fallback classifier
    return this.heuristicClassify(email);
  }

  private heuristicClassify(email: CustomerEmail): ClassificationResult {
    const text = `${email.subject} ${email.body}`.toLowerCase();

    // 1. Refund or Cancellation
    if (/refund|cancel|chargeback|billing dispute|unauthorized charge|terminate our plan|pro-rate|double charge/i.test(text)) {
      return {
        category: "REFUND_OR_CANCELLATION",
        urgency: /urgent|immediately|outrageous|dispute/i.test(text) ? "HIGH" : "MEDIUM",
        risk: "POLICY_FINANCIAL_RISK",
        confidence: 0.96,
        reasoning: "Customer explicitly requested refund, cancellation, or billing adjustment"
      };
    }

    // 2. Complaint
    if (/outrageous|broken|unacceptable|disappointed|down for|lost revenue|feel scammed|misleading/i.test(text)) {
      return {
        category: "COMPLAINT",
        urgency: /outrageous|down|revenue|fix this immediately/i.test(text) ? "CRITICAL" : "HIGH",
        risk: "REPUTATIONAL_RISK",
        confidence: 0.94,
        reasoning: "Expressed dissatisfaction, downtime, or frustration"
      };
    }

    // 3. Quote Request
    if (/quote|how much|cost estimate|pricing plans|what would.*charge|hourly rate/i.test(text)) {
      return {
        category: "QUOTE_REQUEST",
        urgency: "MEDIUM",
        risk: "COMMERCIAL_RISK",
        confidence: 0.92,
        reasoning: "Commercial pricing or scoping quote requested"
      };
    }

    // 4. Project Request
    if (/project|custom.*widget|integrate.*api|native.*app|multi-vendor|web3|scoping call|custom module/i.test(text)) {
      return {
        category: "PROJECT_REQUEST",
        urgency: "MEDIUM",
        risk: "COMMERCIAL_RISK",
        confidence: 0.93,
        reasoning: "Custom software architecture or new feature implementation requested"
      };
    }

    // 5. Follow Up
    if (/following up|checking in|status update|did you receive|ticket #|staging environment/i.test(text)) {
      return {
        category: "FOLLOW_UP",
        urgency: "LOW",
        risk: "SAFE",
        confidence: 0.91,
        reasoning: "Inquiring about previous work, ticket, or deliverable"
      };
    }

    // 6. Troubleshooting
    if (/error|failed|bug|not working|blank page|watermark|spam folder|stuck|glitch|invalid/i.test(text)) {
      return {
        category: "TROUBLESHOOTING",
        urgency: /urgent|immediately/i.test(text) ? "HIGH" : "MEDIUM",
        risk: "SAFE",
        confidence: 0.92,
        reasoning: "Technical error or unexpected system behavior reported"
      };
    }

    // 7. How-To (Default)
    return {
      category: "HOW_TO",
      urgency: "LOW",
      risk: "SAFE",
      confidence: 0.88,
      reasoning: "Product configuration or operational question"
    };
  }
}
