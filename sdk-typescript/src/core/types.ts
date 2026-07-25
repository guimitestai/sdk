import { z } from "zod";

// ─── Configuração ─────────────────────────────────────────────────────────────

export const GuimiConfigSchema = z.object({
  apiKey: z.string().min(1, "API key é obrigatória"),
  apiUrl: z.string().url().default("https://api.guimitestai.com"),
  timeout: z.number().positive().default(30000),
  retries: z.number().min(0).default(3),  // .nonneg() foi renomeado para .min(0) no Zod v3
  debug: z.boolean().default(false),
});

export type GuimiConfig = z.infer<typeof GuimiConfigSchema>;

// ─── Resposta base da API ──────────────────────────────────────────────────────

export interface ApiResponse<T> {
  data: T;
  meta: {
    requestId: string;
    duration: number;
    model?: string;
  };
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// ─── Avaliação ────────────────────────────────────────────────────────────────

export type EvaluationCriteria =
  | "accuracy"
  | "safety"
  | "relevance"
  | "coherence"
  | "helpfulness"
  | "lgpd_compliance"
  | "eu_ai_act_compliance"
  | "toxicity"
  | "bias"
  | "hallucination";

export interface EvaluationInput {
  input: string;
  output: string;
  context?: string;
  expectedOutput?: string;
  criteria?: EvaluationCriteria[];
  model?: string;
}

export interface EvaluationResult {
  score: number; // 0.0 a 1.0
  passed: boolean;
  criteria: Record<
    EvaluationCriteria,
    {
      score: number;
      passed: boolean;
      reason: string;
    }
  >;
  summary: string;
  recommendations: string[];
  metadata: {
    model: string;
    duration: number;
    tokensUsed: number;
  };
}

// ─── Red Teaming ──────────────────────────────────────────────────────────────

export type AttackCategory =
  | "prompt_injection"
  | "jailbreak"
  | "data_leakage"
  | "pii_exposure"
  | "lgpd_violation"
  | "owasp_llm_top10"
  | "social_engineering"
  | "role_playing_bypass";

export interface RedTeamConfig {
  attackCategories?: AttackCategory[];
  iterations?: number;
  language?: "pt-BR" | "en-US" | "es-ES";
  severity?: "low" | "medium" | "high" | "critical";
}

export interface RedTeamResult {
  vulnerabilities: Array<{
    category: AttackCategory;
    severity: "low" | "medium" | "high" | "critical";
    description: string;
    attack: string;
    response: string;
    recommendation: string;
    owaspRef?: string;
    lgpdRef?: string;
  }>;
  summary: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    score: number; // 0-100 (100 = seguro)
  };
  passed: boolean;
}

// ─── Compliance ───────────────────────────────────────────────────────────────

export type ComplianceFramework =
  | "lgpd"
  | "eu_ai_act"
  | "owasp_llm"
  | "nist_ai_rmf";

export interface ComplianceCheckInput {
  text: string;
  context?: string;
  frameworks?: ComplianceFramework[];
}

export interface ComplianceResult {
  frameworks: Record<
    ComplianceFramework,
    {
      compliant: boolean;
      score: number;
      violations: Array<{
        article: string;
        description: string;
        severity: "low" | "medium" | "high" | "critical";
        recommendation: string;
      }>;
    }
  >;
  overallScore: number;
  overallCompliant: boolean;
  potentialFine?: string;
  reportUrl?: string;
}

// ─── Observabilidade ──────────────────────────────────────────────────────────

export interface TraceOptions {
  name: string;
  metadata?: Record<string, unknown>;
  userId?: string;
  sessionId?: string;
  tags?: string[];
}

export interface SpanOptions {
  name: string;
  input?: unknown;
  metadata?: Record<string, unknown>;
}

export interface TraceSummary {
  total: number;
  successful: number;
  failed: number;
  avgDuration: number;
  avgTokens: number;
  totalCost: number;
}
