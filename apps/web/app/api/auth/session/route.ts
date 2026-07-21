import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  ACCESS_COOKIE,
  clearAuthCookies,
  REFRESH_COOKIE,
  setAuthCookies
} from "@/lib/auth-cookies";
import {
  BackendApiError,
  fetchCurrentUser,
  publicAuthError,
  refreshSession,
  validateRequestOrigin
} from "@/lib/auth-server";

export async function GET(request: Request) {
  validateRequestOrigin(request);
  const cookieStore = await cookies();
  const accessToken = cookieStore.get(ACCESS_COOKIE)?.value;
  const refreshToken = cookieStore.get(REFRESH_COOKIE)?.value;

  if (accessToken) {
    try {
      const user = await fetchCurrentUser(accessToken);
      return NextResponse.json({ user });
    } catch (error) {
      if (!(error instanceof BackendApiError) || error.status !== 401) {
        const { status, message } = publicAuthError(error);
        return NextResponse.json({ detail: message }, { status });
      }
    }
  }

  if (!refreshToken) {
    const response = NextResponse.json({ detail: "Sessão não autenticada." }, { status: 401 });
    clearAuthCookies(response);
    return response;
  }

  try {
    const tokens = await refreshSession(refreshToken);
    const user = await fetchCurrentUser(tokens.access_token);
    const response = NextResponse.json({ user });
    setAuthCookies(response, tokens);
    return response;
  } catch (error) {
    const { status, message } = publicAuthError(error);
    const response = NextResponse.json(
      { detail: status === 401 ? "Sua sessão expirou. Entre novamente." : message },
      { status }
    );
    clearAuthCookies(response);
    return response;
  }
}
