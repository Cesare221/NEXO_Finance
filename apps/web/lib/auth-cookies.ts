import type { NextResponse } from "next/server";

const COOKIE_PREFIX = process.env.NODE_ENV === "production" ? "__Host-nexo" : "nexo";
export const ACCESS_COOKIE = `${COOKIE_PREFIX}_access_token`;
export const REFRESH_COOKIE = `${COOKIE_PREFIX}_refresh_token`;
export const MFA_CHALLENGE_COOKIE = `${COOKIE_PREFIX}_mfa_challenge`;

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

const baseCookieOptions = {
  httpOnly: true,
  sameSite: "strict" as const,
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

export function setMfaChallengeCookie(response: NextResponse, challengeToken: string) {
  response.cookies.set(MFA_CHALLENGE_COOKIE, challengeToken, {
    ...baseCookieOptions,
    maxAge: 5 * 60
  });
}

export function clearMfaChallengeCookie(response: NextResponse) {
  response.cookies.set(MFA_CHALLENGE_COOKIE, "", {
    ...baseCookieOptions,
    maxAge: 0
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
  clearMfaChallengeCookie(response);
}
