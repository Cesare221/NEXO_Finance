import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { ACCESS_COOKIE, clearAuthCookies, REFRESH_COOKIE, setAuthCookies } from "@/lib/auth-cookies";
import { authenticatedBackendRequest, publicAuthError, validateRequestOrigin } from "@/lib/auth-server";

export async function DELETE(request: Request, context: { params: Promise<{ sessionId: string }> }) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitação inválida." }, { status: 403 });
  }
  try {
    const { sessionId } = await context.params;
    const cookieStore = await cookies();
    const { tokens } = await authenticatedBackendRequest<void>(
      `/auth/sessions/${encodeURIComponent(sessionId)}`,
      { method: "DELETE" },
      cookieStore.get(ACCESS_COOKIE)?.value,
      cookieStore.get(REFRESH_COOKIE)?.value
    );
    const response = new NextResponse(null, { status: 204 });
    if (tokens) setAuthCookies(response, tokens);
    return response;
  } catch (error) {
    const { status, message } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (status === 401) clearAuthCookies(response);
    return response;
  }
}
