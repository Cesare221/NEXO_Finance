import { NextResponse } from "next/server";
import { backendRequest, publicAuthError, validateRequestOrigin } from "@/lib/auth-server";

export async function POST(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitação inválida." }, { status: 403 });
  }

  try {
    const body = await request.json();
    const data = await backendRequest<{ message: string }>("/auth/password-reset/request", {
      method: "POST",
      body: JSON.stringify(body)
    });
    return NextResponse.json(data, { status: 202 });
  } catch (error) {
    const { status, message, retryAfter } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (retryAfter) response.headers.set("Retry-After", retryAfter);
    return response;
  }
}
