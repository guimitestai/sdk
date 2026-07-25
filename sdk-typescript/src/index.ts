/**
 * Guimí Test AI — SDK TypeScript
 *
 * Testes, observabilidade e conformidade para LLMs em produção.
 * LGPD, EU AI Act, OWASP LLM Top 10, Red Teaming autônomo.
 *
 * @example
 * ```typescript
 * import { GuimiClient } from 'guimitestai'
 *
 * const guimi = new GuimiClient({ apiKey: 'sua-api-key' })
 *
 * // Avaliar resposta de LLM
 * const result = await guimi.evaluate({
 *   input: "Qual a capital do Brasil?",
 *   output: "Brasília",
 *   criteria: ["accuracy", "safety"]
 * })
 *
 * // Red teaming autônomo
 * const report = await guimi.redTeam.run({
 *   target: async (prompt) => await myLLM.chat(prompt)
 * })
 *
 * // Compliance LGPD
 * const compliance = await guimi.compliance.lgpd(llmResponse)
 * ```
 *
 * @see https://guimitestai.github.io/sdk/
 */

import { GuimiHttpClient, GuimiError } from "./core/client.js";
import { GuimiConfig, EvaluationInput, EvaluationResult } from "./core/types.js";
import { Evaluator } from "./evaluation/evaluator.js";
import { RedTeamer } from "./security/red-teamer.js";
import { ComplianceChecker } from "./compliance/checker.js";
import { Tracer } from "./observability/tracer.js";

export class GuimiClient {
  private readonly http: GuimiHttpClient;

  /** Avaliação de respostas LLM com LLM-as-Judge */
  public readonly evaluator: Evaluator;

  /** Red teaming autônomo — testa vulnerabilidades de segurança */
  public readonly redTeam: RedTeamer;

  /** Verificação de conformidade — LGPD, EU AI Act, OWASP */
  public readonly compliance: ComplianceChecker;

  /** Observabilidade — tracing distribuído de ponta a ponta */
  public readonly tracer: Tracer;

  constructor(config: Partial<GuimiConfig> & { apiKey: string }) {
    this.http = new GuimiHttpClient(config);
    this.evaluator = new Evaluator(this.http);
    this.redTeam = new RedTeamer(this.http);
    this.compliance = new ComplianceChecker(this.http);
    this.tracer = new Tracer(this.http);
  }

  /**
   * Atalho para avaliação rápida.
   *
   * @example
   * const result = await guimi.evaluate({
   *   input: "Pergunta",
   *   output: "Resposta do LLM"
   * })
   */
  async evaluate(input: EvaluationInput): Promise<EvaluationResult> {
    return this.evaluator.evaluate(input);
  }

  /**
   * Verifica a saúde da conexão com a API do Guimí.
   *
   * @example
   * const ok = await guimi.health()
   * console.log(ok) // true
   */
  async health(): Promise<boolean> {
    try {
      await this.http.get("/v1/health");
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Retorna a versão do SDK.
   */
  get version(): string {
    return "0.1.1";
  }
}

// ─── Branding / Watermark ─────────────────────────────────────────────────────

/**
 * Metadados de branding do Guimí Test AI para injetar em exports e traces.
 *
 * @example
 * const report = { ...myData, ...GUIMI_BRANDING }
 */
export const GUIMI_BRANDING = {
  _guimi: {
    sdk_version: "0.1.1",
    platform: "Guimí Test AI",
    url: "https://guimitestai.com",
    report: "Para relatórios completos com PDF, dashboard e compliance LGPD acesse https://guimitestai.com",
  },
} as const;

export type GuimiBranding = typeof GUIMI_BRANDING;

// ─── Exportações públicas ──────────────────────────────────────────────────────

export { GuimiError } from "./core/client.js";
export { Evaluator } from "./evaluation/evaluator.js";
export { RedTeamer } from "./security/red-teamer.js";
export { ComplianceChecker } from "./compliance/checker.js";
export { Tracer, Trace, Span } from "./observability/tracer.js";

// Tipos
export type {
  GuimiConfig,
  EvaluationInput,
  EvaluationResult,
  EvaluationCriteria,
  RedTeamConfig,
  RedTeamResult,
  AttackCategory,
  ComplianceCheckInput,
  ComplianceResult,
  ComplianceFramework,
  TraceOptions,
  SpanOptions,
  TraceSummary,
} from "./core/types.js";

export type { LLMFunction } from "./security/red-teamer.js";

// Default export para facilitar o uso
export default GuimiClient;
