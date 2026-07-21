import { NextResponse } from "next/server";
import { setAuthCookies } from "@/lib/auth-cookies";
import {
  authenticate,
  fetchCurrentUser,
  publicAuthError,
  validateRequestOrigin
} from "@/lib/auth-server";

export async function POST(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitação inválida." }, { status: 403 });
  }

  try {
    const body = (await request.json()) as {
      name?: string;
      email?: string;
      password?: string;
    };
    const tokens = await authenticate("/auth/register", body);
    const user = await fetchCurrentUser(tokens.access_token);
    const response = NextResponse.json({ user }, { status: 201 });
    setAuthCookies(response, tokens);
    return response;
  } catch (error) {
    const { status, message, retryAfter } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (retryAfter) response.headers.set("Retry-After", retryAfter);
    return response;
  }
}
