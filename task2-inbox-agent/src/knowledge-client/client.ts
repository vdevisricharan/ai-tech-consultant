import { SourceReference } from "../types.js";

export interface KnowledgeQueryRequest {
  question: string;
  top_k?: number;
  model?: string;
}

export interface KnowledgeQueryResponse {
  answer: string;
  status: "answered" | "insufficient_evidence";
  sources: Array<{
    title: string;
    url: string;
    heading: string;
    relevance: number;
    image_refs: string[];
  }>;
  confidence: number;
  needs_human: boolean;
  tokens_used: number;
  latency_ms: number;
}

export class KnowledgeBrainClient {
  private baseUrl: string;
  private timeoutMs: number;

  constructor(baseUrl: string = process.env.KNOWLEDGE_BRAIN_URL || "http://localhost:8000", timeoutMs: number = 8000) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.timeoutMs = timeoutMs;
  }

  async query(question: string, topK: number = 5): Promise<KnowledgeQueryResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          question,
          top_k: topK
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Knowledge Brain API responded with HTTP ${response.status}`);
      }

      const data = (await response.json()) as KnowledgeQueryResponse;
      return data;
    } catch (err: any) {
      clearTimeout(timeoutId);
      console.warn(`[KnowledgeClient] Query failed (${err.message}). Activating safe fallback.`);
      return {
        answer: "Knowledge Brain service temporarily unreachable. Escalating to human technical team.",
        status: "insufficient_evidence",
        sources: [],
        confidence: 0,
        needs_human: true,
        tokens_used: 0,
        latency_ms: 0
      };
    }
  }

  async checkHealth(): Promise<boolean> {
    try {
      const resp = await fetch(`${this.baseUrl}/api/v1/health`);
      return resp.ok;
    } catch {
      return false;
    }
  }
}
