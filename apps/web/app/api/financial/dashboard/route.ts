import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  ACCESS_COOKIE,
  clearAuthCookies,
  REFRESH_COOKIE,
  setAuthCookies
} from "@/lib/auth-cookies";
import { authenticatedBackendRequest, publicAuthError } from "@/lib/auth-server";

export async function GET(request: Request) {
  try {
    const sourceUrl = new URL(request.url);
    const query = new URLSearchParams();
    for (const key of ["start_date", "end_date", "months"]) {
      const value = sourceUrl.searchParams.get(key);
      if (value) query.set(key, value);
    }

    const cookieStore = await cookies();
    const { data, tokens } = await authenticatedBackendRequest(
      `/financial/dashboard${query.size ? `?${query}` : ""}`,
      { method: "GET" },
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
