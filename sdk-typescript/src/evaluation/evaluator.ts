import { GuimiHttpClient } from "../core/client.js";
import {
  EvaluationInput,
  EvaluationResult,
  EvaluationCriteria,
} from "../core/types.js";

export class Evaluator {
  private readonly DEFAULT_CRITERIA: EvaluationCriteria[] = [
    "accuracy",
    "safety",
    "relevance",
    "coherence",
  ];

  constructor(private readonly client: GuimiHttpClient) {}

  /**
   * Avalia uma resposta de LLM usando LLM-as-Judge.
   *
   * @example
   * const result = await guimi.evaluate({
   *   input: "Qual a capital do Brasil?",
   *   output: "Brasília",
   *   criteria: ["accuracy", "safety"]
   * })
   * console.log(result.score) // 0.95
   * console.log(result.passed) // true
   */
  async evaluate(input: EvaluationInput): Promise<EvaluationResult> {
    const payload = {
      ...input,
      criteria: input.criteria ?? this.DEFAULT_CRITERIA,
    };

    const response = await this.client.post<EvaluationResult>(
      "/v1/evaluate",
      payload
    );

    return response.data;
  }

  /**
   * Avalia múltiplas respostas em lote.
   *
   * @example
   * const results = await guimi.evaluateBatch([
   *   { input: "Pergunta 1", output: "Resposta 1" },
   *   { input: "Pergunta 2", output: "Resposta 2" },
   * ])
   */
  async evaluateBatch(inputs: EvaluationInput[]): Promise<EvaluationResult[]> {
    const response = await this.client.post<EvaluationResult[]>(
      "/v1/evaluate/batch",
      { inputs }
    );

    return response.data;
  }

  /**
   * Verifica rapidamente se uma resposta é segura (sem avaliação completa).
   * Mais rápido e barato que evaluate() completo.
   *
   * @example
   * const safe = await guimi.isSafe("Resposta do LLM aqui")
   * if (!safe) throw new Error("Resposta insegura!")
   */
  async isSafe(output: string): Promise<boolean> {
    const result = await this.evaluate({
      input: "",
      output,
      criteria: ["safety", "toxicity"],
    });

    return result.passed;
  }

  /**
   * Detecta alucinações comparando com o contexto fornecido.
   *
   * @example
   * const score = await guimi.hallucinationScore({
   *   output: "Resposta do LLM",
   *   context: "Contexto real da base de conhecimento"
   * })
   * console.log(score) // 0.1 = 10% de alucinação
   */
  async hallucinationScore(input: {
    output: string;
    context: string;
  }): Promise<number> {
    const result = await this.evaluate({
      input: "",
      output: input.output,
      context: input.context,
      criteria: ["hallucination"],
    });

    return result.criteria["hallucination"]?.score ?? 0;
  }
}
