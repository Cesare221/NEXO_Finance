import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { ACCESS_COOKIE, clearAuthCookies, REFRESH_COOKIE } from "@/lib/auth-cookies";
import { authenticatedBackendRequest, publicAuthError, validateRequestOrigin } from "@/lib/auth-server";

export async function DELETE(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitação inválida." }, { status: 403 });
  }
  try {
    const cookieStore = await cookies();
    await authenticatedBackendRequest<void>(
      "/auth/me",
      { method: "DELETE", body: JSON.stringify(await request.json()) },
      cookieStore.get(ACCESS_COOKIE)?.value,
      cookieStore.get(REFRESH_COOKIE)?.value
    );
    const response = new NextResponse(null, { status: 204 });
    clearAuthCookies(response);
    return response;
  } catch (error) {
    const { status, message } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (status === 401) clearAuthCookies(response);
    return response;
  }
}
