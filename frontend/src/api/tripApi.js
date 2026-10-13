const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(code, message, details = null, status = 0) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

/** POST /api/routes/analyze. Resolves with the contract response, rejects with ApiError. */
export async function analyzeRoutes(payload, { signal } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/routes/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new ApiError(
      "NETWORK_ERROR",
      "Could not reach the server. Check your connection and try again.",
    );
  }

  let body = null;
  try {
    body = await response.json();
  } catch {
    // non-JSON body; handled below
  }

  if (!response.ok) {
    const e = body?.error;
    throw new ApiError(
      e?.code ?? "UNKNOWN_ERROR",
      e?.message ?? `Request failed (HTTP ${response.status}).`,
      e?.details ?? null,
      response.status,
    );
  }
  return body;
}
