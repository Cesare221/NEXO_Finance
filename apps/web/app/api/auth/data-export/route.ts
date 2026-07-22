import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { ACCESS_COOKIE, clearAuthCookies, REFRESH_COOKIE, setAuthCookies } from "@/lib/auth-cookies";
import { authenticatedBackendRequest, publicAuthError } from "@/lib/auth-server";

export async function GET() {
  try {
    const cookieStore = await cookies();
    const { data, tokens } = await authenticatedBackendRequest<Record<string, unknown>>(
      "/auth/me/export",
      { method: "GET" },
      cookieStore.get(ACCESS_COOKIE)?.value,
      cookieStore.get(REFRESH_COOKIE)?.value
    );
    const response = NextResponse.json(data, {
      headers: {
        "Cache-Control": "no-store",
        "Content-Disposition": 'attachment; filename="nexo-meus-dados.json"'
      }
    });
    if (tokens) setAuthCookies(response, tokens);
    return response;
  } catch (error) {
    const { status, message } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (status === 401) clearAuthCookies(response);
    return response;
  }
}
