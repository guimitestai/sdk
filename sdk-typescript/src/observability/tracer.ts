import { randomUUID } from "node:crypto";
import { GuimiHttpClient } from "../core/client.js";
import { TraceOptions, SpanOptions, TraceSummary } from "../core/types.js";

export class Span {
  private startTime: number;
  private endTime?: number;
  private output?: unknown;
  private error?: Error;

  constructor(
    private readonly client: GuimiHttpClient,
    private readonly traceId: string,
    private readonly spanId: string,
    public readonly name: string,
    public readonly input?: unknown
  ) {
    this.startTime = Date.now();
  }

  /**
   * Finaliza o span com sucesso.
   */
  async end(output?: unknown): Promise<void> {
    this.endTime = Date.now();
    this.output = output;

    await this.client.post("/v1/traces/spans/end", {
      traceId: this.traceId,
      spanId: this.spanId,
      output,
      duration: this.endTime - this.startTime,
      status: "success",
    }).catch(() => {
      // Falha silenciosa — observabilidade não deve quebrar o app
    });
  }

  /**
   * Finaliza o span com erro.
   */
  async fail(error: Error): Promise<void> {
    this.endTime = Date.now();
    this.error = error;

    await this.client.post("/v1/traces/spans/end", {
      traceId: this.traceId,
      spanId: this.spanId,
      error: { message: error.message, stack: error.stack },
      duration: this.endTime - this.startTime,
      status: "error",
    }).catch(() => {
      // Falha silenciosa
    });
  }

  get duration(): number {
    return (this.endTime ?? Date.now()) - this.startTime;
  }
}

export class Trace {
  private spans: Span[] = [];

  constructor(
    private readonly client: GuimiHttpClient,
    public readonly traceId: string,
    public readonly name: string
  ) {}

  /**
   * Cria um span dentro desta trace.
   *
   * @example
   * const span = trace.span({ name: "llm-call", input: prompt })
   * const response = await llm.chat(prompt)
   * await span.end(response)
   */
  span(options: SpanOptions): Span {
    const spanId = randomUUID();
    const span = new Span(
      this.client,
      this.traceId,
      spanId,
      options.name,
      options.input
    );
    this.spans.push(span);
    return span;
  }

  /**
   * Executa uma função dentro de um span automaticamente.
   * O span é finalizado com sucesso ou erro automaticamente.
   *
   * @example
   * const result = await trace.withSpan("llm-call", prompt, async () => {
   *   return await llm.chat(prompt)
   * })
   */
  async withSpan<T>(
    name: string,
    input: unknown,
    fn: () => Promise<T>
  ): Promise<T> {
    const span = this.span({ name, input });
    try {
      const result = await fn();
      await span.end(result);
      return result;
    } catch (err) {
      await span.fail(err instanceof Error ? err : new Error(String(err)));
      throw err;
    }
  }
}

export class Tracer {
  constructor(private readonly client: GuimiHttpClient) {}

  /**
   * Cria uma nova trace para monitorar uma operação completa.
   *
   * @example
   * const trace = await guimi.tracer.trace({
   *   name: "chat-completion",
   *   userId: "user-123"
   * })
   * const span = trace.span({ name: "llm-call", input: prompt })
   * const response = await llm.chat(prompt)
   * await span.end(response)
   */
  async trace(options: TraceOptions): Promise<Trace> {
    const response = await this.client.post<{ traceId: string }>(
      "/v1/traces",
      options
    ).catch(() => ({ data: { traceId: randomUUID() } }));

    return new Trace(this.client, response.data.traceId, options.name);
  }

  /**
   * Executa uma função dentro de uma trace automaticamente.
   * Ideal para wrapping de chamadas LLM completas.
   *
   * @example
   * const result = await guimi.tracer.withTrace("chat", async (trace) => {
   *   const span = trace.span({ name: "llm-call", input: prompt })
   *   const response = await llm.chat(prompt)
   *   await span.end(response)
   *   return response
   * })
   */
  async withTrace<T>(
    name: string,
    fn: (trace: Trace) => Promise<T>,
    options?: Omit<TraceOptions, "name">
  ): Promise<T> {
    const trace = await this.trace({ name, ...options });
    return fn(trace);
  }

  /**
   * Retorna o resumo de todas as traces.
   *
   * @example
   * const summary = await guimi.tracer.summary()
   * console.log(summary.total) // 1523
   * console.log(summary.avgDuration) // 245ms
   * console.log(summary.totalCost) // $12.45
   */
  async summary(): Promise<TraceSummary> {
    const response = await this.client.get<TraceSummary>("/v1/traces/summary");
    return response.data;
  }
}
