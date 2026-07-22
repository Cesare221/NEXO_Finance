import { NextRequest, NextResponse } from "next/server";

const protectedRoutes = [
  "/onboarding",
  "/dashboard",
  "/contas",
  "/cartoes",
  "/transacoes",
  "/categorias",
  "/fin",
  "/configuracoes"
];

const cookiePrefix = process.env.NODE_ENV === "production" ? "__Host-nexo" : "nexo";
const accessCookie = `${cookiePrefix}_access_token`;
const refreshCookie = `${cookiePrefix}_refresh_token`;

export function middleware(request: NextRequest) {
  const protectedRoute = protectedRoutes.some(
    (route) => request.nextUrl.pathname === route || request.nextUrl.pathname.startsWith(`${route}/`)
  );
  if (!protectedRoute) return NextResponse.next();

  const accessToken = request.cookies.get(accessCookie)?.value;
  const refreshToken = request.cookies.get(refreshCookie)?.value;
  if (accessToken || refreshToken) return NextResponse.next();

  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("next", `${request.nextUrl.pathname}${request.nextUrl.search}`);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    "/onboarding/:path*",
    "/dashboard/:path*",
    "/contas/:path*",
    "/cartoes/:path*",
    "/transacoes/:path*",
    "/categorias/:path*",
    "/fin/:path*",
    "/configuracoes/:path*"
  ]
};
