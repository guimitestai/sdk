import { describe, it, expect, vi, beforeEach } from "vitest";
import { GuimiClient, GuimiError } from "../src/index.js";

// Mock do fetch global
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function mockResponse<T>(data: T, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () =>
      Promise.resolve(
        status >= 200 && status < 300
          ? { data, meta: { requestId: "test-123", duration: 100 } }
          : data
      ),
  });
}

describe("GuimiClient", () => {
  let guimi: GuimiClient;

  beforeEach(() => {
    guimi = new GuimiClient({ apiKey: "test-key-123" });
    mockFetch.mockReset();
  });

  // ─── Configuração ────────────────────────────────────────────────────────────

  describe("Configuração", () => {
    it("deve inicializar com apiKey obrigatória", () => {
      expect(() => new GuimiClient({ apiKey: "key" })).not.toThrow();
    });

    it("deve rejeitar apiKey vazia", () => {
      expect(() => new GuimiClient({ apiKey: "" })).toThrow();
    });

    it("deve ter versão definida", () => {
      expect(guimi.version).toBe("0.1.1");
    });

    it("deve ter todos os módulos disponíveis", () => {
      expect(guimi.evaluator).toBeDefined();
      expect(guimi.redTeam).toBeDefined();
      expect(guimi.compliance).toBeDefined();
      expect(guimi.tracer).toBeDefined();
    });
  });

  // ─── Health ───────────────────────────────────────────────────────────────────

  describe("health()", () => {
    it("deve retornar true quando API está disponível", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse({ status: "ok" }));
      const ok = await guimi.health();
      expect(ok).toBe(true);
    });

    it("deve retornar false quando API está indisponível", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Connection refused"));
      const ok = await guimi.health();
      expect(ok).toBe(false);
    });
  });

  // ─── Avaliação ────────────────────────────────────────────────────────────────

  describe("evaluate()", () => {
    const mockResult = {
      score: 0.95,
      passed: true,
      criteria: {
        accuracy: { score: 0.98, passed: true, reason: "Resposta correta" },
        safety: { score: 0.99, passed: true, reason: "Sem conteúdo nocivo" },
        relevance: { score: 0.92, passed: true, reason: "Relevante" },
        coherence: { score: 0.91, passed: true, reason: "Coerente" },
      },
      summary: "Resposta de alta qualidade",
      recommendations: [],
      metadata: { model: "gpt-4o", duration: 1200, tokensUsed: 450 },
    };

    it("deve avaliar uma resposta de LLM", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(mockResult));

      const result = await guimi.evaluate({
        input: "Qual a capital do Brasil?",
        output: "Brasília",
      });

      expect(result.score).toBe(0.95);
      expect(result.passed).toBe(true);
    });

    it("deve usar critérios padrão quando não especificados", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(mockResult));

      await guimi.evaluate({
        input: "Pergunta",
        output: "Resposta",
      });

      const body = JSON.parse(mockFetch.mock.calls[0]?.[1]?.body as string);
      expect(body.criteria).toContain("accuracy");
      expect(body.criteria).toContain("safety");
    });

    it("deve aceitar critérios customizados", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(mockResult));

      await guimi.evaluate({
        input: "Pergunta",
        output: "Resposta",
        criteria: ["lgpd_compliance", "hallucination"],
      });

      const body = JSON.parse(mockFetch.mock.calls[0]?.[1]?.body as string);
      expect(body.criteria).toContain("lgpd_compliance");
    });
  });

  // ─── Compliance LGPD ─────────────────────────────────────────────────────────

  describe("compliance.lgpd()", () => {
    it("deve verificar conformidade LGPD", async () => {
      mockFetch.mockResolvedValueOnce(
        mockResponse({
          frameworks: {
            lgpd: {
              compliant: true,
              score: 92,
              violations: [],
            },
          },
          overallScore: 92,
          overallCompliant: true,
          potentialFine: "R$ 0",
        })
      );

      const result = await guimi.compliance.lgpd("Texto sem dados pessoais");
      expect(result.compliant).toBe(true);
      expect(result.score).toBe(92);
      expect(result.violations).toHaveLength(0);
    });

    it("deve detectar violações de LGPD", async () => {
      mockFetch.mockResolvedValueOnce(
        mockResponse({
          frameworks: {
            lgpd: {
              compliant: false,
              score: 30,
              violations: [
                {
                  article: "Art. 6º III",
                  description: "Coleta excessiva de dados",
                  severity: "high",
                  recommendation: "Minimizar dados coletados",
                },
              ],
            },
          },
          overallScore: 30,
          overallCompliant: false,
          potentialFine: "R$ 50.000.000",
        })
      );

      const result = await guimi.compliance.lgpd("CPF: 123.456.789-00");
      expect(result.compliant).toBe(false);
      expect(result.violations.length).toBeGreaterThan(0);
    });
  });

  // ─── Erros ────────────────────────────────────────────────────────────────────

  describe("Tratamento de erros", () => {
    it("deve lançar GuimiError em resposta HTTP 401", async () => {
      mockFetch.mockResolvedValueOnce(
        mockResponse(
          { code: "UNAUTHORIZED", message: "API key inválida" },
          401
        )
      );

      await expect(
        guimi.evaluate({ input: "test", output: "test" })
      ).rejects.toThrow(GuimiError);
    });

    it("deve lançar GuimiError com timeout", async () => {
      // Simular timeout via AbortError
      mockFetch.mockRejectedValueOnce(
        Object.assign(new Error("The operation was aborted"), {
          name: "AbortError",
        })
      );

      await expect(
        guimi.evaluate({ input: "test", output: "test" })
      ).rejects.toThrow(GuimiError);
    });
  });

  // ─── Tracer ───────────────────────────────────────────────────────────────────

  describe("tracer", () => {
    it("deve criar uma trace", async () => {
      mockFetch.mockResolvedValueOnce(
        mockResponse({ traceId: "trace-abc-123" })
      );

      const trace = await guimi.tracer.trace({ name: "test-trace" });
      expect(trace.traceId).toBe("trace-abc-123");
      expect(trace.name).toBe("test-trace");
    });

    it("deve criar span dentro de trace", async () => {
      mockFetch.mockResolvedValueOnce(
        mockResponse({ traceId: "trace-abc-123" })
      );
      mockFetch.mockResolvedValueOnce(mockResponse({ ok: true }));

      const trace = await guimi.tracer.trace({ name: "test-trace" });
      const span = trace.span({ name: "llm-call", input: "prompt" });

      expect(span.name).toBe("llm-call");
      expect(span.duration).toBeGreaterThanOrEqual(0);
    });

    it("deve retornar summary das traces", async () => {
      const mockSummary = {
        total: 1523,
        successful: 1498,
        failed: 25,
        avgDuration: 245,
        avgTokens: 380,
        totalCost: 12.45,
      };

      mockFetch.mockResolvedValueOnce(mockResponse(mockSummary));

      const summary = await guimi.tracer.summary();
      expect(summary.total).toBe(1523);
      expect(summary.totalCost).toBe(12.45);
    });
  });
});
