import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { AuthTokens, clearMfaChallengeCookie, MFA_CHALLENGE_COOKIE, setAuthCookies } from "@/lib/auth-cookies";
import {
  backendRequest,
  fetchCurrentUser,
  publicAuthError,
  validateRequestOrigin
} from "@/lib/auth-server";

export async function POST(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitação inválida." }, { status: 403 });
  }

  const cookieStore = await cookies();
  const challengeToken = cookieStore.get(MFA_CHALLENGE_COOKIE)?.value;

  if (!challengeToken) {
    return NextResponse.json(
      { detail: "Desafio de MFA expirado ou não encontrado. Faça login novamente." },
      { status: 400 }
    );
  }

  try {
    const body = (await request.json()) as { code?: string };
    const tokens = await backendRequest<AuthTokens>("/auth/mfa/challenge", {
      method: "POST",
      body: JSON.stringify({
        challenge_token: challengeToken,
        code: body.code ?? ""
      })
    });

    const user = await fetchCurrentUser(tokens.access_token);
    const response = NextResponse.json({ status: "authenticated", user });
    setAuthCookies(response, tokens);
    clearMfaChallengeCookie(response);
    return response;
  } catch (error) {
    const { status, message, retryAfter } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (retryAfter) response.headers.set("Retry-After", retryAfter);
    return response;
  }
}
