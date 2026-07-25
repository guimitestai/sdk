import { GuimiHttpClient } from "../core/client.js";
import { RedTeamConfig, RedTeamResult } from "../core/types.js";

export type LLMFunction = (prompt: string) => Promise<string>;

export class RedTeamer {
  constructor(private readonly client: GuimiHttpClient) {}

  /**
   * Executa red teaming autônomo contra uma função LLM.
   * Gera ataques automaticamente e testa vulnerabilidades.
   *
   * @example
   * const report = await guimi.redTeam({
   *   target: async (prompt) => await myLLM.chat(prompt),
   *   config: { language: "pt-BR", severity: "high" }
   * })
   * console.log(report.summary.score) // 87 (de 100)
   * console.log(report.passed) // true
   */
  async run(options: {
    target: LLMFunction;
    config?: RedTeamConfig;
  }): Promise<RedTeamResult> {
    // 1. Registrar a sessão de red teaming
    const session = await this.client.post<{ sessionId: string; attacks: string[] }>(
      "/v1/red-team/session",
      {
        config: options.config ?? {},
        language: options.config?.language ?? "pt-BR",
      }
    );

    const { sessionId, attacks } = session.data;

    // 2. Executar cada ataque contra o target
    const results: Array<{ attack: string; response: string }> = [];

    for (const attack of attacks) {
      try {
        const response = await options.target(attack);
        results.push({ attack, response });
      } catch (err) {
        results.push({
          attack,
          response: `ERROR: ${err instanceof Error ? err.message : String(err)}`,
        });
      }
    }

    // 3. Analisar resultados no servidor
    const analysis = await this.client.post<RedTeamResult>(
      "/v1/red-team/analyze",
      { sessionId, results }
    );

    return analysis.data;
  }

  /**
   * Testa especificamente vulnerabilidades de LGPD.
   * Verifica exposição de CPF, dados pessoais, decisões automatizadas.
   *
   * @example
   * const report = await guimi.redTeamLGPD({
   *   target: async (prompt) => await myLLM.chat(prompt)
   * })
   */
  async runLGPD(options: { target: LLMFunction }): Promise<RedTeamResult> {
    return this.run({
      target: options.target,
      config: {
        attackCategories: ["pii_exposure", "lgpd_violation", "data_leakage"],
        language: "pt-BR",
        severity: "critical",
      },
    });
  }

  /**
   * Testa as 10 vulnerabilidades do OWASP LLM Top 10.
   *
   * @example
   * const report = await guimi.redTeamOWASP({
   *   target: async (prompt) => await myLLM.chat(prompt)
   * })
   */
  async runOWASP(options: { target: LLMFunction }): Promise<RedTeamResult> {
    return this.run({
      target: options.target,
      config: {
        attackCategories: ["owasp_llm_top10"],
        severity: "high",
      },
    });
  }
}
