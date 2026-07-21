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

async function mutateCategory(
  request: Request,
  categoryId: string,
  method: "PUT" | "DELETE"
) {
  if (!validateRequestOrigin(request)) {
    return NextResponse.json({ detail: "Origem da solicitacao invalida." }, { status: 403 });
  }

  try {
    const cookieStore = await cookies();
    const body = method === "PUT" ? JSON.stringify(await request.json()) : undefined;
    const { data, tokens } = await authenticatedBackendRequest(
      `/financial/categories/${encodeURIComponent(categoryId)}`,
      { method, body },
      cookieStore.get(ACCESS_COOKIE)?.value,
      cookieStore.get(REFRESH_COOKIE)?.value
    );
    const response = NextResponse.json(data);
    if (tokens) setAuthCookies(response, tokens);
    return response;
  } catch (error) {
    const { status, message } = publicAuthError(error);
    const response = NextResponse.json({ detail: message }, { status });
    if (status === 401) clearAuthCookies(response);
    return response;
  }
}

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ categoryId: string }> }
) {
  const { categoryId } = await params;
  return mutateCategory(request, categoryId, "PUT");
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ categoryId: string }> }
) {
  const { categoryId } = await params;
  return mutateCategory(request, categoryId, "DELETE");
}
