import { NextResponse } from "next/server";
import { clearMfaChallengeCookie, setAuthCookies, setMfaChallengeCookie } from "@/lib/auth-cookies";
import {
  authenticateLogin,
  fetchCurrentUser,
  publicAuthError,
  validateRequestOrigin
} from "@/lib/auth-server";

export async function POST(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitação inválida." }, { status: 403 });
  }

  try {
    const body = (await request.json()) as { email?: string; password?: string };
    const outcome = await authenticateLogin(body, request.headers.get("user-agent"));

    if (outcome.status === "mfa_required") {
      const response = NextResponse.json({ status: "mfa_required" });
      if (outcome.challenge_token) {
        setMfaChallengeCookie(response, outcome.challenge_token);
      }
      return response;
    }

    if (outcome.status === "email_verification_required") {
      return NextResponse.json({
        status: "email_verification_required",
        email: outcome.email
      });
    }

    if (outcome.access_token && outcome.refresh_token) {
      const user = await fetchCurrentUser(outcome.access_token);
      const response = NextResponse.json({ status: "authenticated", user });
      setAuthCookies(response, {
        access_token: outcome.access_token,
        refresh_token: outcome.refresh_token,
        token_type: outcome.token_type ?? "bearer"
      });
      clearMfaChallengeCookie(response);
      return response;
    }

    return NextResponse.json({ detail: "Não foi possível concluir o login." }, { status: 400 });
  } catch (error) {
    const { status, message, retryAfter } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (retryAfter) response.headers.set("Retry-After", retryAfter);
    return response;
  }
}
