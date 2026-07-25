export function validateWebRuntime(env = process.env) {
  if (env.NODE_ENV !== "production") return;
  // Only validate API_URL when it is explicitly provided (real deployments).
  // Local builds without a deployed backend are allowed to skip this.
  const apiUrl = env.API_URL;
  if (apiUrl && !apiUrl.startsWith("https://")) {
    throw new Error("API_URL must be an explicit HTTPS URL in production");
  }
}
