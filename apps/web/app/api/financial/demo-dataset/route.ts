import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  ACCESS_COOKIE,
  clearAuthCookies,
  REFRESH_COOKIE,
  setAuthCookies
} from "@/lib/auth-cookies";
import {
  authenticatedBackendRequest,
  publicAuthError,
  validateRequestOrigin
} from "@/lib/auth-server";
import type { DemoDatasetState } from "@/lib/financial-types";

async function requestBackend(method: "GET" | "POST" | "DELETE") {
  const cookieStore = await cookies();
  const { data, tokens, status } = await authenticatedBackendRequest<DemoDatasetState>(
    "/financial/demo-dataset",
    { method },
    cookieStore.get(ACCESS_COOKIE)?.value,
    cookieStore.get(REFRESH_COOKIE)?.value
  );
  const response = NextResponse.json(data, { status });
  if (tokens) setAuthCookies(response, tokens);
  return response;
}

function errorResponse(error: unknown) {
  const { status, message } = publicAuthError(error);
  const response = NextResponse.json({ detail: message }, { status });
  if (status === 401) clearAuthCookies(response);
  return response;
}

export async function GET() {
  try {
    return await requestBackend("GET");
  } catch (error) {
    return errorResponse(error);
  }
}

export async function POST(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json(
      { detail: "Origem da solicitacao invalida." },
      { status: 403 }
    );
  }
  try {
    return await requestBackend("POST");
  } catch (error) {
    return errorResponse(error);
  }
}

export async function DELETE(request: Request) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json(
      { detail: "Origem da solicitacao invalida." },
      { status: 403 }
    );
  }
  try {
    return await requestBackend("DELETE");
  } catch (error) {
    return errorResponse(error);
  }
}
