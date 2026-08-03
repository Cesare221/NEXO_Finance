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

export async function GET(request: Request) {
  try {
    const status = new URL(request.url).searchParams.get("status");
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    const cookieStore = await cookies();
    const { data, tokens } = await authenticatedBackendRequest(
      `/assistant/proposals${query}`,
      { method: "GET" },
      cookieStore.get(ACCESS_COOKIE)?.value,
      cookieStore.get(REFRESH_COOKIE)?.value
    );
    const response = NextResponse.json(data);
    if (tokens) setAuthCookies(response, tokens);
    return response;
  } catch (error) {
    const { status, message } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (status === 401) clearAuthCookies(response);
    return response;
  }
}

export async function POST(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitacao invalida." }, { status: 403 });
  }

  try {
    const body = await request.json();
    const cookieStore = await cookies();
    const { data, tokens } = await authenticatedBackendRequest(
      "/assistant/proposals",
      { method: "POST", body: JSON.stringify(body) },
      cookieStore.get(ACCESS_COOKIE)?.value,
      cookieStore.get(REFRESH_COOKIE)?.value
    );
    const response = NextResponse.json(data, { status: 201 });
    if (tokens) setAuthCookies(response, tokens);
    return response;
  } catch (error) {
    const { status, message } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (status === 401) clearAuthCookies(response);
    return response;
  }
}
