import type { AuthTokens } from "@/lib/auth-cookies";

const API_BASE_URL =
  process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type SessionUser = {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  avatar_data_url: string | null;
  theme_preference: "system" | "light" | "dark";
};

export class BackendApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly retryAfter?: string
  ) {
    super(message);
    this.name = "BackendApiError";
  }
}

async function backendRequest<T>(
  path: string,
  init: RequestInit,
  onResponse?: (response: Response) => void
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store"
  });
  onResponse?.(response);

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: unknown };
    const message =
      response.status === 422
        ? "Confira os dados informados e respeite os requisitos dos campos."
        : typeof body.detail === "string"
          ? body.detail
          : "Não foi possível concluir a solicitação.";
    throw new BackendApiError(
      message,
      response.status,
      response.headers.get("Retry-After") ?? undefined
    );
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function authenticate(
  path: "/auth/login" | "/auth/register",
  credentials: Record<string, unknown>
) {
  return backendRequest<AuthTokens>(path, {
    method: "POST",
    body: JSON.stringify(credentials)
  });
}

export function fetchCurrentUser(accessToken: string) {
  return backendRequest<SessionUser>("/auth/me", {
    method: "GET",
    headers: { Authorization: `Bearer ${accessToken}` }
  });
}

export function refreshSession(refreshToken: string) {
  return backendRequest<AuthTokens>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken })
  });
}

export function revokeSession(accessToken: string, refreshToken: string) {
  return backendRequest<void>("/auth/logout", {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
}

export async function authenticatedBackendRequest<T>(
  path: string,
  init: RequestInit,
  accessToken?: string,
  refreshToken?: string
) {
  let currentAccessToken = accessToken;
  let refreshedTokens: AuthTokens | undefined;
  let responseStatus = 200;

  if (!currentAccessToken && refreshToken) {
    refreshedTokens = await refreshSession(refreshToken);
    currentAccessToken = refreshedTokens.access_token;
  }
  if (!currentAccessToken) {
    throw new BackendApiError("Sessão não autenticada.", 401);
  }

  const requestWithAuthorization = (token: string) => {
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${token}`);
    return backendRequest<T>(
      path,
      { ...init, headers },
      (response) => {
        responseStatus = response.status;
      }
    );
  };

  try {
    const data = await requestWithAuthorization(currentAccessToken);
    return { data, tokens: refreshedTokens, status: responseStatus };
  } catch (error) {
    if (!(error instanceof BackendApiError) || error.status !== 401 || !refreshToken) {
      throw error;
    }
    refreshedTokens = await refreshSession(refreshToken);
    const data = await requestWithAuthorization(refreshedTokens.access_token);
    return { data, tokens: refreshedTokens, status: responseStatus };
  }
}

export function validateRequestOrigin(request: Request) {
  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite === "cross-site") return false;

  const origin = request.headers.get("origin");
  if (!origin) return true;

  const forwardedHost = request.headers.get("x-forwarded-host");
  const host = forwardedHost ?? request.headers.get("host");
  if (!host) return false;

  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}

export function publicAuthError(error: unknown) {
  if (error instanceof BackendApiError) {
    return {
      status: error.status,
      message: error.message,
      retryAfter: error.retryAfter
    };
  }
  return {
    status: 503,
    message: "Serviço temporariamente indisponível. Tente novamente.",
    retryAfter: undefined
  };
}
