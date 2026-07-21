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

export function middleware(request: NextRequest) {
  const protectedRoute = protectedRoutes.some(
    (route) => request.nextUrl.pathname === route || request.nextUrl.pathname.startsWith(`${route}/`)
  );
  if (!protectedRoute) return NextResponse.next();

  const accessToken = request.cookies.get("fin_access_token")?.value;
  const refreshToken = request.cookies.get("fin_refresh_token")?.value;
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
