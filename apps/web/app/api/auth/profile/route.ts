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

export async function PATCH(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitacao invalida." }, { status: 403 });
  }

  try {
    const cookieStore = await cookies();
    const { data, tokens } = await authenticatedBackendRequest(
      "/auth/me",
      { method: "PATCH", body: JSON.stringify(await request.json()) },
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
