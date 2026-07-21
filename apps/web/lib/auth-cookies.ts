import type { NextResponse } from "next/server";

export const ACCESS_COOKIE = "fin_access_token";
export const REFRESH_COOKIE = "fin_refresh_token";

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

const baseCookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/"
};

export function setAuthCookies(response: NextResponse, tokens: AuthTokens) {
  response.cookies.set(ACCESS_COOKIE, tokens.access_token, {
    ...baseCookieOptions,
    maxAge: 15 * 60
  });
  response.cookies.set(REFRESH_COOKIE, tokens.refresh_token, {
    ...baseCookieOptions,
    maxAge: 7 * 24 * 60 * 60
  });
}

export function clearAuthCookies(response: NextResponse) {
  response.cookies.set(ACCESS_COOKIE, "", {
    ...baseCookieOptions,
    maxAge: 0
  });
  response.cookies.set(REFRESH_COOKIE, "", {
    ...baseCookieOptions,
    maxAge: 0
  });
}
