import { createHmac } from "crypto";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

function gatewayBase(): string {
  return (
    process.env.EGG_GATEWAY_BASE_URL?.replace(/\/$/, "") ??
    "http://localhost:9000/gruponeural/egg/gateway"
  );
}

function pad2(n: number) {
  return String(n).padStart(2, "0");
}

/** Formato YYYYMMDDHHmm em UTC (alinhado ao gateway Java). */
function formatTimestampYYYYMMDDHHmm(date = new Date()): string {
  const y = date.getUTCFullYear();
  const m = pad2(date.getUTCMonth() + 1);
  const d = pad2(date.getUTCDate());
  const hh = pad2(date.getUTCHours());
  const mm = pad2(date.getUTCMinutes());
  return `${y}${m}${d}${hh}${mm}`;
}

function isSafeSegment(segment: string) {
  return /^[a-zA-Z0-9._-]+$/.test(segment);
}

async function proxy(request: NextRequest, pathSegments: string[]) {
  if (!pathSegments.length) {
    return NextResponse.json({ error: "Caminho ausente" }, { status: 400 });
  }
  if (!pathSegments.every(isSafeSegment)) {
    return NextResponse.json({ error: "Caminho inválido" }, { status: 400 });
  }

  const path = pathSegments.join("/");
  const target = new URL(`${gatewayBase()}/${path}`);
  request.nextUrl.searchParams.forEach((v, k) => target.searchParams.set(k, v));

  const headers = new Headers();
  headers.set("Accept", "application/json");

  const secret = process.env.EGG_GATEWAY_SIGNATURE_SECRET;
  if (!secret) {
    return NextResponse.json(
      {
        mensagemTipo: "falha",
        mensagemTitulo: "Configuração ausente.",
        mensagemDetalhe: "Defina EGG_GATEWAY_SIGNATURE_SECRET no .env.local.",
      },
      { status: 500 }
    );
  }

  const timestamp = formatTimestampYYYYMMDDHHmm();
  const signature = createHmac("sha256", secret).update(timestamp).digest("hex");
  headers.set("X-Signature", signature);
  headers.set("X-Timestamp", timestamp);
  headers.set("X-Correlation-ID", crypto.randomUUID());

  const method = request.method.toUpperCase();
  const init: RequestInit = { method, headers, cache: "no-store" };

  if (method === "POST" || method === "PUT" || method === "PATCH") {
    const contentType = request.headers.get("Content-Type") ?? "";
    if (contentType.includes("multipart/form-data")) {
      const raw = await request.arrayBuffer();
      if (raw.byteLength > 0) {
        headers.set("Content-Type", contentType);
        init.body = raw;
      }
    } else {
      const raw = await request.text();
      if (raw.length > 0) {
        headers.set("Content-Type", contentType || "application/json");
        init.body = raw;
      }
    }
  }

  try {
    const res = await fetch(target, init);
    const contentType = res.headers.get("Content-Type") ?? "application/json";
    const body = await res.arrayBuffer();
    const outHeaders = new Headers({ "Content-Type": contentType });
    const corrIdOut = headers.get("X-Correlation-ID");
    if (corrIdOut) outHeaders.set("X-Correlation-ID", corrIdOut);
    return new NextResponse(body, { status: res.status, headers: outHeaders });
  } catch {
    return NextResponse.json(
      {
        mensagemTipo: "falha",
        mensagemTitulo: "Sem conexão com o gateway.",
        mensagemDetalhe: "Verifique se Gateway, BFF e Processador estão ativos.",
      },
      { status: 503 }
    );
  }
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  return proxy(request, path);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  return proxy(request, path);
}
