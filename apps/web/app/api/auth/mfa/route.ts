import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { ACCESS_COOKIE, clearAuthCookies, REFRESH_COOKIE } from "@/lib/auth-cookies";
import { authenticatedBackendRequest, publicAuthError, validateRequestOrigin } from "@/lib/auth-server";

export async function DELETE(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitação inválida." }, { status: 403 });
  }

  const cookieStore = await cookies();
  const accessToken = cookieStore.get(ACCESS_COOKIE)?.value;
  const refreshToken = cookieStore.get(REFRESH_COOKIE)?.value;

  try {
    const body = await request.json();
    const { data } = await authenticatedBackendRequest<{ message: string }>(
      "/auth/mfa",
      { method: "DELETE", body: JSON.stringify(body) },
      accessToken,
      refreshToken
    );

    const response = NextResponse.json(data);
    clearAuthCookies(response);
    return response;
  } catch (error) {
    const { status, message, retryAfter } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (retryAfter) response.headers.set("Retry-After", retryAfter);
    return response;
  }
}
