import { NextResponse } from "next/server";
import {
  authenticateRegister,
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
      privacy_accepted?: boolean;
      ai_data_processing_consent?: boolean;
    };
    const outcome = await authenticateRegister(body, request.headers.get("user-agent"));
    return NextResponse.json(
      { status: outcome.status, email: outcome.email },
      { status: 201 }
    );
  } catch (error) {
    const { status, message, retryAfter } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (retryAfter) response.headers.set("Retry-After", retryAfter);
    return response;
  }
}
