import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  ACCESS_COOKIE,
  clearAuthCookies,
  REFRESH_COOKIE,
  setAuthCookies
} from "@/lib/auth-cookies";
import {
  authenticatedBackendRequest,
  publicAuthError,
  validateRequestOrigin
} from "@/lib/auth-server";

async function requestBackend(path: string, init: RequestInit) {
  const cookieStore = await cookies();
  const { data, tokens } = await authenticatedBackendRequest(
    path,
    init,
    cookieStore.get(ACCESS_COOKIE)?.value,
    cookieStore.get(REFRESH_COOKIE)?.value
  );
  const response = NextResponse.json(data, { status: init.method === "POST" ? 201 : 200 });
  if (tokens) setAuthCookies(response, tokens);
  return response;
}

function errorResponse(error: unknown) {
  const { status, message } = publicAuthError(error);
  const response = NextResponse.json({ detail: message }, { status });
  if (status === 401) clearAuthCookies(response);
  return response;
}

export async function GET(request: Request) {
  try {
    const sourceUrl = new URL(request.url);
    const query = new URLSearchParams();
    for (const key of ["type", "account_id", "category_id", "start_date", "end_date"]) {
      const value = sourceUrl.searchParams.get(key);
      if (value) query.set(key, value);
    }
    return await requestBackend(
      `/financial/transactions${query.size ? `?${query}` : ""}`,
      { method: "GET" }
    );
  } catch (error) {
    return errorResponse(error);
  }
}

export async function POST(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitação inválida." }, { status: 403 });
  }

  try {
    const body = await request.json();
    return await requestBackend(
      "/financial/transactions",
      { method: "POST", body: JSON.stringify(body) }
    );
  } catch (error) {
    return errorResponse(error);
  }
}
