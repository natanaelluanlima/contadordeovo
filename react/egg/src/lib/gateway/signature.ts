import { createHmac } from "crypto";

function pad2(n: number) {
  return String(n).padStart(2, "0");
}

/** Formato YYYYMMDDHHmm em UTC (alinhado ao gateway Java). */
export function formatTimestampYYYYMMDDHHmm(date = new Date()): string {
  const y = date.getUTCFullYear();
  const m = pad2(date.getUTCMonth() + 1);
  const d = pad2(date.getUTCDate());
  const hh = pad2(date.getUTCHours());
  const mm = pad2(date.getUTCMinutes());
  return `${y}${m}${d}${hh}${mm}`;
}

export function buildGatewayHeaders(extra?: HeadersInit): Headers {
  const secret = process.env.EGG_GATEWAY_SIGNATURE_SECRET;
  if (!secret) {
    throw new Error("Defina EGG_GATEWAY_SIGNATURE_SECRET no .env.local");
  }
  const timestamp = formatTimestampYYYYMMDDHHmm();
  const signature = createHmac("sha256", secret).update(timestamp).digest("hex");
  const headers = new Headers(extra);
  headers.set("X-Signature", signature);
  headers.set("X-Timestamp", timestamp);
  headers.set("X-Correlation-ID", crypto.randomUUID());
  return headers;
}

export function gatewayBaseUrl(): string {
  return (
    process.env.EGG_GATEWAY_BASE_URL?.replace(/\/$/, "") ??
    "http://localhost:9000/gruponeural/egg/gateway"
  );
}
