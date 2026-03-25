export type IssueType = "bug" | "security" | "performance";
export type Severity = "low" | "medium" | "high";

export interface Issue {
  type: IssueType;
  line: number;
  severity: Severity;
  message: string;
}

export interface ReviewResponse {
  issues: Issue[];
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? "20000");
const API_MAX_RETRIES = Number(import.meta.env.VITE_API_MAX_RETRIES ?? "1");

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function parseResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type")?.toLowerCase() ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return { detail: text || "Request failed." };
}

async function requestWithTimeout(code: string, language: string): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

  try {
    return await fetch(`${API_BASE_URL}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, language }),
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

export async function reviewCode(code: string, language: string): Promise<ReviewResponse> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= API_MAX_RETRIES; attempt += 1) {
    try {
      const response = await requestWithTimeout(code, language);
      const payload = (await parseResponseBody(response)) as { detail?: unknown; issues?: unknown };

      if (!response.ok) {
        const detail = typeof payload?.detail === "string" ? payload.detail : "Review request failed.";

        const isRetryableStatus = [502, 503, 504].includes(response.status);
        if (isRetryableStatus && attempt < API_MAX_RETRIES) {
          await sleep(400 * (attempt + 1));
          continue;
        }

        throw new Error(detail);
      }

      if (!Array.isArray(payload?.issues)) {
        throw new Error("Backend response format is invalid.");
      }

      return payload as ReviewResponse;
    } catch (error) {
      const isAbort = error instanceof DOMException && error.name === "AbortError";
      const message = isAbort
        ? `Request timed out after ${Math.round(API_TIMEOUT_MS / 1000)} seconds.`
        : error instanceof Error
          ? error.message
          : "Unexpected network error.";

      lastError = new Error(message);

      if (attempt < API_MAX_RETRIES) {
        await sleep(400 * (attempt + 1));
        continue;
      }
    }
  }

  throw lastError ?? new Error("Review request failed.");
}