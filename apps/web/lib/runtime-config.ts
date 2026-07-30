export function validateWebRuntime(env = process.env) {
  if (env.NODE_ENV !== "production") return;
  // Only validate API_URL when it is explicitly provided (real deployments).
  // Local production builds may still point at a local API for validation.
  const apiUrl = env.API_URL;
  if (!apiUrl) return;

  let parsed: URL;
  try {
    parsed = new URL(apiUrl);
  } catch {
    throw new Error("API_URL must be a valid URL");
  }

  const isLocalhost = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";
  if (parsed.protocol !== "https:" && !(parsed.protocol === "http:" && isLocalhost)) {
    throw new Error("API_URL must be an explicit HTTPS URL in production");
  }
}
