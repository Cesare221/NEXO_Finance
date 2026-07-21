import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  ACCESS_COOKIE,
  clearAuthCookies,
  REFRESH_COOKIE,
  setAuthCookies
} from "@/lib/auth-cookies";
import {
  refreshSession,
  revokeSession,
  validateRequestOrigin
} from "@/lib/auth-server";

export async function POST(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitação inválida." }, { status: 403 });
  }

  const cookieStore = await cookies();
  let accessToken = cookieStore.get(ACCESS_COOKIE)?.value;
  let refreshToken = cookieStore.get(REFRESH_COOKIE)?.value;

  if (refreshToken && !accessToken) {
    try {
      const tokens = await refreshSession(refreshToken);
      accessToken = tokens.access_token;
      refreshToken = tokens.refresh_token;
    } catch {
      // Local cookies are still cleared when the remote session is already invalid.
    }
  }

  if (accessToken && refreshToken) {
    try {
      await revokeSession(accessToken, refreshToken);
    } catch {
      // Logout remains successful locally even when the API cannot be reached.
    }
  }

  const response = new NextResponse(null, { status: 204 });
  clearAuthCookies(response);
  return response;
}
