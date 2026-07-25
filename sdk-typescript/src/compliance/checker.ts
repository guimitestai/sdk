import { GuimiHttpClient } from "../core/client.js";
import {
  ComplianceCheckInput,
  ComplianceResult,
  ComplianceFramework,
} from "../core/types.js";

export class ComplianceChecker {
  constructor(private readonly client: GuimiHttpClient) {}

  /**
   * Verifica conformidade com múltiplos frameworks regulatórios.
   *
   * @example
   * const result = await guimi.compliance.check({
   *   text: "Resposta do LLM aqui",
   *   frameworks: ["lgpd", "eu_ai_act"]
   * })
   * console.log(result.overallCompliant) // true/false
   * console.log(result.overallScore) // 0-100
   */
  async check(input: ComplianceCheckInput): Promise<ComplianceResult> {
    const payload = {
      ...input,
      frameworks: input.frameworks ?? ["lgpd", "eu_ai_act", "owasp_llm"],
    };

    const response = await this.client.post<ComplianceResult>(
      "/v1/compliance/check",
      payload
    );

    return response.data;
  }

  /**
   * Verificação específica de LGPD.
   * Analisa exposição de dados pessoais, decisões automatizadas (Art. 20),
   * minimização de dados (Art. 6º III) e transparência (Art. 6º VI).
   *
   * @example
   * const result = await guimi.compliance.lgpd("Resposta do chatbot")
   * if (!result.compliant) {
   *   console.log(result.violations) // lista de violações por artigo
   * }
   */
  async lgpd(text: string): Promise<{
    compliant: boolean;
    score: number;
    violations: ComplianceResult["frameworks"]["lgpd"]["violations"];
    potentialFine: string;
  }> {
    const result = await this.check({ text, frameworks: ["lgpd"] });
    const lgpdResult = result.frameworks["lgpd"];

    return {
      compliant: lgpdResult?.compliant ?? false,
      score: lgpdResult?.score ?? 0,
      violations: lgpdResult?.violations ?? [],
      potentialFine: result.potentialFine ?? "R$ 0",
    };
  }

  /**
   * Verificação específica de EU AI Act.
   * Classifica o sistema de IA por nível de risco e verifica conformidade.
   *
   * @example
   * const result = await guimi.compliance.euAiAct("Resposta do sistema de IA")
   * console.log(result.riskLevel) // "high" | "limited" | "minimal"
   */
  async euAiAct(text: string): Promise<{
    compliant: boolean;
    score: number;
    riskLevel: "unacceptable" | "high" | "limited" | "minimal";
    violations: ComplianceResult["frameworks"]["eu_ai_act"]["violations"];
  }> {
    const result = await this.check({ text, frameworks: ["eu_ai_act"] });
    const euResult = result.frameworks["eu_ai_act"];

    return {
      compliant: euResult?.compliant ?? false,
      score: euResult?.score ?? 0,
      riskLevel: "limited",
      violations: euResult?.violations ?? [],
    };
  }

  /**
   * Gera relatório completo de conformidade em PDF.
   * Ideal para auditorias, DPO e documentação regulatória.
   *
   * @example
   * const report = await guimi.compliance.generateReport({
   *   text: "Resposta do LLM",
   *   frameworks: ["lgpd", "eu_ai_act"]
   * })
   * console.log(report.url) // URL do PDF gerado
   */
  async generateReport(
    input: ComplianceCheckInput & { title?: string }
  ): Promise<{ url: string; expiresAt: Date }> {
    const response = await this.client.post<{
      url: string;
      expiresAt: string;
    }>("/v1/compliance/report", input);

    return {
      url: response.data.url,
      expiresAt: new Date(response.data.expiresAt),
    };
  }

  /**
   * Verifica se um texto contém dados pessoais (PII).
   * Detecta CPF, RG, e-mail, telefone, endereço, dados bancários.
   *
   * @example
   * const pii = await guimi.compliance.detectPII("Meu CPF é 123.456.789-00")
   * console.log(pii.found) // true
   * console.log(pii.types) // ["cpf"]
   */
  async detectPII(text: string): Promise<{
    found: boolean;
    types: string[];
    count: number;
    redacted: string;
  }> {
    const response = await this.client.post<{
      found: boolean;
      types: string[];
      count: number;
      redacted: string;
    }>("/v1/compliance/pii-detect", { text });

    return response.data;
  }

  /**
   * Verifica conformidade com OWASP LLM Top 10.
   */
  async owasp(text: string): Promise<{
    compliant: boolean;
    score: number;
    violations: ComplianceResult["frameworks"]["owasp_llm"]["violations"];
  }> {
    const result = await this.check({ text, frameworks: ["owasp_llm"] });
    const owaspResult = result.frameworks["owasp_llm"];

    return {
      compliant: owaspResult?.compliant ?? false,
      score: owaspResult?.score ?? 0,
      violations: owaspResult?.violations ?? [],
    };
  }
}

// Tipos auxiliares exportados
export type { ComplianceFramework, ComplianceCheckInput, ComplianceResult };
