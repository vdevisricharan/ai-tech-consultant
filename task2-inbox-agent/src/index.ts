import express, { Request, Response } from "express";
import path from "path";
import fs from "fs";
import { InboxAgent } from "./agent.js";
import { CustomerEmail, HumanAction } from "./types.js";

const app = express();
const port = parseInt(process.env.PORT || "3000", 10);

app.use(express.json());
app.use(express.static(path.resolve("public")));

// Initialize Inbox Agent
const agent = new InboxAgent({
  knowledgeBrainUrl: process.env.KNOWLEDGE_BRAIN_URL || "http://localhost:8000",
  storageDir: "data"
});

// Load 50 realistic emails dataset
const emailsFilePath = path.resolve("data", "emails.json");
let emailsCache: CustomerEmail[] = [];
if (fs.existsSync(emailsFilePath)) {
  try {
    emailsCache = JSON.parse(fs.readFileSync(emailsFilePath, "utf-8"));
  } catch (err) {
    console.error("[Server] Error reading emails.json:", err);
  }
}

// Routes
app.get("/api/inbox/emails", (_req: Request, res: Response) => {
  res.json(emailsCache);
});

app.post("/api/inbox/process", async (req: Request, res: Response) => {
  try {
    const email = req.body as CustomerEmail;
    const result = await agent.processEmail(email);
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/inbox/review", (req: Request, res: Response) => {
  try {
    const { emailId, action, finalReply, notes } = req.body as {
      emailId: string;
      action: HumanAction;
      finalReply: string;
      notes?: string;
    };

    const email = emailsCache.find(e => e.id === emailId);
    const category = email ? (email as any).category : "HOW_TO";

    const feedback = agent.submitHumanReview(
      emailId,
      category,
      finalReply,
      finalReply,
      action,
      notes
    );
    res.json(feedback);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/inbox/autonomy", (_req: Request, res: Response) => {
  res.json(agent.learningEngine.getAllAutonomyStatuses());
});

app.get("/health", (_req: Request, res: Response) => {
  res.json({
    status: "healthy",
    service: "Inbox Agent Service & Portal UI",
    timestamp: new Date().toISOString()
  });
});

app.listen(port, () => {
  console.log(`[InboxAgent] Web Portal UI & Service listening at http://localhost:${port}`);
});
