export type ContagemTrack = {
  track_id: number;
  label: string;
  confidence: number;
  bbox: [number, number, number, number];
};

export type ContagemStatus = {
  state: string;
  mode: string;
  total_count: number;
  active_tracks: number;
  fps: number;
  annotated_frame_b64?: string | null;
  frame_width?: number;
  frame_height?: number;
  line?: { x1: number; y1: number; x2: number; y2: number };
  tracks?: ContagemTrack[];
  skipped?: boolean;
  events?: Array<{
    track_id: number;
    label: string;
    total_count: number;
    timestamp: number;
  }>;
};

type GatewayErrorBody = {
  mensagemTitulo?: string;
  mensagemDetalhe?: string;
  detail?: string;
};

async function readGatewayError(res: Response, fallback: string): Promise<string> {
  try {
    const body = (await res.json()) as GatewayErrorBody;
    const title = body.mensagemTitulo ?? body.detail;
    const detail = body.mensagemDetalhe;
    if (title && detail) return `${title} ${detail}`;
    if (title) return title;
  } catch {
    /* corpo não-JSON */
  }
  return fallback;
}

async function gatewayFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = `/api/gateway/${path.replace(/^\//, "")}`;
  return fetch(url, { ...init, cache: "no-store" });
}

export async function fetchContagemStatus(): Promise<ContagemStatus> {
  const res = await gatewayFetch("contagem/screen/status");
  if (!res.ok) {
    throw new Error(await readGatewayError(res, `Status HTTP ${res.status}`));
  }
  return res.json();
}

export async function iniciarContagem(mode = "browser_camera"): Promise<ContagemStatus> {
  const res = await gatewayFetch("contagem/screen/iniciar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  if (!res.ok) {
    throw new Error(await readGatewayError(res, `Iniciar falhou: HTTP ${res.status}`));
  }
  return res.json();
}

export async function pararContagem(): Promise<ContagemStatus> {
  const res = await gatewayFetch("contagem/screen/parar", { method: "POST" });
  if (!res.ok) {
    throw new Error(await readGatewayError(res, `Parar falhou: HTTP ${res.status}`));
  }
  return res.json();
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result;
      if (typeof dataUrl !== "string") {
        reject(new Error("Falha ao ler frame"));
        return;
      }
      const comma = dataUrl.indexOf(",");
      resolve(comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl);
    };
    reader.onerror = () => reject(reader.error ?? new Error("Falha ao ler frame"));
    reader.readAsDataURL(blob);
  });
}

export async function enviarFrameBase64(image_b64: string): Promise<ContagemStatus> {
  const res = await gatewayFetch("contagem/screen/frame-b64", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_b64 }),
  });
  if (!res.ok) {
    throw new Error(await readGatewayError(res, `Frame falhou: HTTP ${res.status}`));
  }
  return res.json();
}

export async function enviarFrame(blob: Blob): Promise<ContagemStatus> {
  const image_b64 = await blobToBase64(blob);
  return enviarFrameBase64(image_b64);
}

/** Encerra processador, BFF, gateway, site e o launcher local. */
export async function desligarContador(): Promise<void> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 4000);
  try {
    const res = await fetch("http://127.0.0.1:8010/api/shutdown", {
      method: "POST",
      cache: "no-store",
      signal: controller.signal,
    });
    if (!res.ok) {
      throw new Error(`Falha ao desligar (HTTP ${res.status})`);
    }
  } finally {
    window.clearTimeout(timer);
  }
}
