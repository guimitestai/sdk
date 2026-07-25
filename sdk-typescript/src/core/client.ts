import { GuimiConfig, GuimiConfigSchema, ApiResponse, ApiError } from "./types.js";

export class GuimiHttpClient {
  private readonly config: GuimiConfig;

  constructor(config: Partial<GuimiConfig> & { apiKey: string }) {
    this.config = GuimiConfigSchema.parse(config);
  }

  getConfig(): Readonly<GuimiConfig> {
    return Object.freeze({ ...this.config });
  }

  async request<T>(
    method: "GET" | "POST" | "PUT" | "DELETE",
    path: string,
    body?: unknown
  ): Promise<ApiResponse<T>> {
    const url = `${this.config.apiUrl}${path}`;

    const controller = new AbortController();
    const timeoutMs: number = this.config.timeout;
    const timeoutId = setTimeout(
      () => controller.abort(),
      timeoutMs
    );

    try {
      const fetchOptions: RequestInit = {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.config.apiKey}`,
          "X-SDK-Language": "typescript",
          "X-SDK-Version": "0.1.0",
        },
        signal: controller.signal,
      };

      if (body !== undefined) {
        fetchOptions.body = JSON.stringify(body);
      }

      const response = await fetch(url, fetchOptions);

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = (await response.json()) as ApiError;
        throw new GuimiError(
          error.message ?? `HTTP ${response.status}`,
          error.code ?? "HTTP_ERROR",
          response.status,
          error.details
        );
      }

      return (await response.json()) as ApiResponse<T>;
    } catch (err) {
      clearTimeout(timeoutId);

      if (err instanceof GuimiError) throw err;

      if (err instanceof Error && err.name === "AbortError") {
        throw new GuimiError(
          `Timeout após ${this.config.timeout}ms`,
          "TIMEOUT",
          408
        );
      }

      throw new GuimiError(
        `Erro de rede: ${err instanceof Error ? err.message : String(err)}`,
        "NETWORK_ERROR",
        0
      );
    }
  }

  async post<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
    return this.request<T>("POST", path, body);
  }

  async get<T>(path: string): Promise<ApiResponse<T>> {
    return this.request<T>("GET", path);
  }
}

export class GuimiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "GuimiError";
  }
}
