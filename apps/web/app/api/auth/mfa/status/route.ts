import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { ACCESS_COOKIE, REFRESH_COOKIE, setAuthCookies } from "@/lib/auth-cookies";
import { authenticatedBackendRequest, publicAuthError, validateRequestOrigin } from "@/lib/auth-server";

export async function GET(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitação inválida." }, { status: 403 });
  }

  const cookieStore = await cookies();
  const accessToken = cookieStore.get(ACCESS_COOKIE)?.value;
  const refreshToken = cookieStore.get(REFRESH_COOKIE)?.value;

  try {
    const { data, tokens } = await authenticatedBackendRequest<{ enabled: boolean; activated_at: string | null }>(
      "/auth/mfa/status",
      { method: "GET" },
      accessToken,
      refreshToken
    );

    const response = NextResponse.json(data);
    if (tokens) setAuthCookies(response, tokens);
    return response;
  } catch (error) {
    const { status, message, retryAfter } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (retryAfter) response.headers.set("Retry-After", retryAfter);
    return response;
  }
}
