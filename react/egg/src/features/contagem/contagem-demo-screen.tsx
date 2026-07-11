"use client";

import Image from "next/image";
import {
  Building2,
  CalendarCheck,
  Camera,
  ChevronDown,
  Clock,
  Egg,
  FileText,
  FileVideo,
  Layers,
  Menu,
  Pause,
  Play,
  PlayCircle,
  Power,
  RefreshCw,
  RotateCcw,
  ScanEye,
  Square,
  Video,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import {
  enviarFrameBase64,
  fetchContagemStatus,
  iniciarContagem,
  pararContagem,
  type ContagemStatus,
  type ContagemTrack,
} from "@/lib/gateway/contagem-api";
import { generateContagemReportPdf } from "@/lib/reports/contagem-report-pdf";

const DAILY_STORAGE_KEY = "contador-ovos-daily-total";
const GRANJA_STORAGE_KEY = "contador-ovos-granja";
const LOTE_STORAGE_KEY = "contador-ovos-lote";

const GRANJA_OPTIONS = [
  "VANDERLEI ODY - VO",
  "VANDERLEI ODY - VV",
  "VANDERLEI ODY - VL",
  "MARCOS ODY - MO",
  "LAUREDIR BRUSTOLIN - LL",
] as const;

function formatVideoTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "00:00";
  const total = Math.floor(seconds);
  const minutes = Math.floor(total / 60);
  const secs = total % 60;
  return `${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function readStoredGranja(): string {
  if (typeof window === "undefined") return GRANJA_OPTIONS[0];
  return localStorage.getItem(GRANJA_STORAGE_KEY) ?? GRANJA_OPTIONS[0];
}

function readStoredLote(): { digits: string; siglas: string } {
  if (typeof window === "undefined") return { digits: "0000", siglas: "AA" };
  try {
    const raw = localStorage.getItem(LOTE_STORAGE_KEY);
    if (!raw) return { digits: "0000", siglas: "AA" };
    const parsed = JSON.parse(raw) as { digits?: string; siglas?: string };
    return {
      digits: (parsed.digits ?? "0000").replace(/\D/g, "").slice(0, 4).padStart(4, "0"),
      siglas: (parsed.siglas ?? "AA").replace(/[^a-zA-Z]/g, "").slice(0, 2).toUpperCase(),
    };
  } catch {
    return { digits: "0000", siglas: "AA" };
  }
}

function writeStoredLote(digits: string, siglas: string) {
  localStorage.setItem(LOTE_STORAGE_KEY, JSON.stringify({ digits, siglas }));
}

const MAX_CAPTURE_WIDTH = 960;
const UPLOAD_JPEG_QUALITY = 0.68;
const MIN_FRAME_INTERVAL_MS = 45;
const VIDEO_SAMPLE_SECONDS = 0.033;
const BOX_LERP_MS = 35;

type SmoothTrack = ContagemTrack & {
  from: [number, number, number, number];
  to: [number, number, number, number];
  updatedAt: number;
};

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function lerpBbox(
  from: [number, number, number, number],
  to: [number, number, number, number],
  t: number
): [number, number, number, number] {
  return [
    lerp(from[0], to[0], t),
    lerp(from[1], to[1], t),
    lerp(from[2], to[2], t),
    lerp(from[3], to[3], t),
  ];
}

function captureFrameBase64(video: HTMLVideoElement, canvas: HTMLCanvasElement): string | null {
  const width = video.videoWidth;
  const height = video.videoHeight;
  if (!width || !height) return null;

  const scale = width > MAX_CAPTURE_WIDTH ? MAX_CAPTURE_WIDTH / width : 1;
  const targetW = Math.max(1, Math.round(width * scale));
  const targetH = Math.max(1, Math.round(height * scale));

  canvas.width = targetW;
  canvas.height = targetH;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  ctx.drawImage(video, 0, 0, targetW, targetH);

  const dataUrl = canvas.toDataURL("image/jpeg", UPLOAD_JPEG_QUALITY);
  const comma = dataUrl.indexOf(",");
  return comma >= 0 ? dataUrl.slice(comma + 1) : null;
}

function seekVideoTo(video: HTMLVideoElement, timeSeconds: number): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!Number.isFinite(video.duration) && video.readyState < 1) {
      reject(new Error("Vídeo ainda não está pronto para seek."));
      return;
    }

    const target = Math.max(0, timeSeconds);
    if (Math.abs(video.currentTime - target) < 0.02 && video.readyState >= 2) {
      resolve();
      return;
    }

    const onSeeked = () => {
      cleanup();
      resolve();
    };
    const onError = () => {
      cleanup();
      reject(new Error("Falha ao posicionar o vídeo."));
    };
    const cleanup = () => {
      video.removeEventListener("seeked", onSeeked);
      video.removeEventListener("error", onError);
    };

    video.addEventListener("seeked", onSeeked);
    video.addEventListener("error", onError);
    video.currentTime = target;
  });
}

function getLocalDateKey(date = new Date()) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function readDailyTotal(): number {
  if (typeof window === "undefined") return 0;

  try {
    const raw = localStorage.getItem(DAILY_STORAGE_KEY);
    if (!raw) return 0;
    const parsed = JSON.parse(raw) as { date: string; total: number };
    return parsed.date === getLocalDateKey() ? parsed.total : 0;
  } catch {
    return 0;
  }
}

function writeDailyTotal(total: number) {
  localStorage.setItem(
    DAILY_STORAGE_KEY,
    JSON.stringify({ date: getLocalDateKey(), total })
  );
}

type CameraDevice = {
  deviceId: string;
  label: string;
};

type InfoCardProps = {
  title: string;
  value?: string;
  icon: ReactNode;
  accent?: "default" | "success" | "danger";
  children?: ReactNode;
};

function InfoCard({ title, value, icon, accent = "default", children }: InfoCardProps) {
  const valueColor =
    accent === "success"
      ? "text-value-success"
      : accent === "danger"
        ? "text-value-danger"
        : "text-[var(--rovah-text)]";

  return (
    <article className="info-card-3d flex min-h-[72px] flex-col items-center justify-center px-2 py-1.5 text-center">
      <div className="info-card-icon mb-0.5 flex h-6 w-6 items-center justify-center rounded-full [&_svg]:h-3.5 [&_svg]:w-3.5">
        {icon}
      </div>
      <div className="text-[9px] font-semibold uppercase leading-tight tracking-wide text-[var(--rovah-text-muted)]">
        {title}
      </div>
      {children ?? (
        <div className={`mt-0.5 text-lg font-bold leading-none md:text-xl ${valueColor}`}>{value}</div>
      )}
    </article>
  );
}

function VideoDurationOverlay({
  currentTime,
  duration,
}: {
  currentTime: number;
  duration: number;
}) {
  const progress = duration > 0 ? Math.min(100, (currentTime / duration) * 100) : 0;

  return (
    <div className="pointer-events-none absolute inset-x-2 bottom-2 rounded-md border border-white/20 bg-slate-950/85 px-2 py-1 shadow-lg backdrop-blur-sm">
      <div className="flex items-center justify-between gap-2 text-[10px] text-slate-200">
        <span>Vídeo</span>
        <span className="font-semibold text-white">
          {formatVideoTime(currentTime)} / {formatVideoTime(duration)}
        </span>
      </div>
      <div className="mt-1 h-1 overflow-hidden rounded-full bg-[var(--rovah-dark-soft)]">
        <div
          className="video-progress-bar h-full rounded-full transition-[width] duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

function DateTimeCard({ dateTime }: { dateTime: Date }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  const date = dateTime.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
  const time = dateTime.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <div className="datetime-chip shrink-0 leading-tight">
      <span className="datetime-chip-label flex items-center gap-1">
        <Clock className="h-3 w-3" strokeWidth={2} />
        Tempo real
      </span>
      <span className="datetime-chip-date">{mounted ? date : "--/--/----"}</span>
      <span className="datetime-chip-time">{mounted ? time : "--:--:--"}</span>
    </div>
  );
}

type MenuItemProps = {
  icon: ReactNode;
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  tone?: "default" | "primary" | "success" | "danger";
};

function ControlButton({
  icon,
  label,
  onClick,
  disabled,
  tone = "default",
}: {
  icon: ReactNode;
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  tone?: "default" | "primary" | "success" | "danger" | "warning";
}) {
  const toneClass =
    tone === "success"
      ? "border-emerald-400/60 bg-emerald-500/20 text-emerald-100 hover:bg-emerald-500/35 hover:border-emerald-300"
      : tone === "danger"
        ? "border-rose-400/60 bg-rose-500/20 text-rose-100 hover:bg-rose-500/35 hover:border-rose-300"
        : tone === "warning"
          ? "border-amber-400/60 bg-amber-500/20 text-amber-100 hover:bg-amber-500/35 hover:border-amber-300"
          : tone === "primary"
            ? "border-sky-400/60 bg-sky-500/20 text-sky-100 hover:bg-sky-500/35 hover:border-sky-300"
            : "border-slate-400/50 bg-slate-500/20 text-slate-100 hover:bg-slate-500/35";

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      aria-label={label}
      title={label}
      className={`flex h-11 w-11 items-center justify-center rounded-full border-2 shadow-lg backdrop-blur-md transition hover:scale-105 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:scale-100 sm:h-12 sm:w-12 ${toneClass}`}
    >
      {icon}
    </button>
  );
}

function MenuItem({ icon, label, onClick, disabled, tone = "default" }: MenuItemProps) {
  const toneClass =
    tone === "primary"
      ? "text-[var(--rovah-green-dark)] hover:bg-[rgba(155,203,59,0.12)]"
      : tone === "success"
        ? "text-[var(--rovah-green-dark)] hover:bg-[rgba(155,203,59,0.12)]"
        : tone === "danger"
          ? "text-red-600 hover:bg-red-50"
          : "text-[var(--rovah-text)] hover:bg-[var(--rovah-bg)]";

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-45 ${toneClass}`}
    >
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md border border-[var(--rovah-border)] bg-white text-[var(--rovah-green-dark)] [&_svg]:h-3.5 [&_svg]:w-3.5">
        {icon}
      </span>
      <span>{label}</span>
    </button>
  );
}

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function waitForVideoDimensions(video: HTMLVideoElement, timeoutMs = 8000): Promise<void> {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    if (video.videoWidth > 0 && video.videoHeight > 0 && video.readyState >= 2) {
      return;
    }
    await wait(100);
  }
  throw new Error(
    "A câmera não entregou vídeo válido. Se usar DroidCam, abra o app no celular e conecte antes de iniciar."
  );
}

function isLikelyBlankFeed(ctx: CanvasRenderingContext2D, width: number, height: number): boolean {
  const sampleW = Math.min(width, 48);
  const sampleH = Math.min(height, 48);
  const { data } = ctx.getImageData(0, 0, sampleW, sampleH);
  const pixels = data.length / 4;
  if (!pixels) return true;

  let sumR = 0;
  let sumG = 0;
  let sumB = 0;
  for (let i = 0; i < data.length; i += 4) {
    sumR += data[i];
    sumG += data[i + 1];
    sumB += data[i + 2];
  }

  const avgR = sumR / pixels;
  const avgG = sumG / pixels;
  const avgB = sumB / pixels;

  let variance = 0;
  for (let i = 0; i < data.length; i += 4) {
    variance +=
      Math.abs(data[i] - avgR) + Math.abs(data[i + 1] - avgG) + Math.abs(data[i + 2] - avgB);
  }
  variance /= pixels;

  const mostlyGreen = avgG > avgR * 1.15 && avgG > avgB * 1.15;
  const mostlyDark = avgR < 30 && avgG < 30 && avgB < 30;
  return variance < 18 && (mostlyGreen || mostlyDark);
}

export function ContagemDemoScreen() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const previewCanvasRef = useRef<HTMLCanvasElement>(null);
  const processorCanvasRef = useRef<HTMLCanvasElement>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileUrlRef = useRef<string | null>(null);
  const loopRef = useRef<number | null>(null);
  const previewLoopRef = useRef<number | null>(null);
  const countingLoopActiveRef = useRef(false);
  const frameProcessingRef = useRef(false);
  const pendingFrameRef = useRef<{ imageB64: string; videoTime: number } | null>(null);
  const lastFrameSentAtRef = useRef(0);
  const lastProcessedVideoTimeRef = useRef(0);
  const videoFileNameRef = useRef<string | null>(null);
  const overlayRef = useRef<{
    tracks: SmoothTrack[];
    line: ContagemStatus["line"] | null;
    frameWidth: number;
    frameHeight: number;
    totalCount: number;
  }>({
    tracks: [],
    line: null,
    frameWidth: 0,
    frameHeight: 0,
    totalCount: 0,
  });
  const fileInputRef = useRef<HTMLInputElement>(null);
  const activeDeviceIdRef = useRef<string | null>(null);
  const sessionStartedAtRef = useRef<Date | null>(null);
  const sessionPreparedRef = useRef(false);

  const [status, setStatus] = useState<ContagemStatus | null>(null);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [preparingPipeline, setPreparingPipeline] = useState(false);
  const [pipelineReady, setPipelineReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasProcessorOverlay, setHasProcessorOverlay] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [videoFileName, setVideoFileName] = useState<string | null>(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [cameras, setCameras] = useState<CameraDevice[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState("");
  const [loadingCameras, setLoadingCameras] = useState(false);
  const [sourceWarning, setSourceWarning] = useState<string | null>(null);
  const [streamInfo, setStreamInfo] = useState<string | null>(null);
  const [previewOnly, setPreviewOnly] = useState(false);
  const [activeDeviceId, setActiveDeviceId] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [paused, setPaused] = useState(false);
  const [completedDailyTotal, setCompletedDailyTotal] = useState(0);
  const [now, setNow] = useState(() => new Date());
  const [videoDuration, setVideoDuration] = useState(0);
  const [videoCurrentTime, setVideoCurrentTime] = useState(0);
  const [selectedGranja, setSelectedGranja] = useState<string>(GRANJA_OPTIONS[0]);
  const [loteDigits, setLoteDigits] = useState("0000");
  const [loteSiglas, setLoteSiglas] = useState("AA");
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    videoFileNameRef.current = videoFileName;
  }, [videoFileName]);

  const updateProcessorOverlay = useCallback((data: ContagemStatus) => {
    const now = performance.now();
    const previous = new Map(overlayRef.current.tracks.map((track) => [track.track_id, track]));
    const nextTracks: SmoothTrack[] = (data.tracks ?? []).map((track) => {
      const bbox = track.bbox;
      const existing = previous.get(track.track_id);
      if (!existing) {
        return {
          ...track,
          from: bbox,
          to: bbox,
          updatedAt: now,
        };
      }
      const progress = Math.min(1, (now - existing.updatedAt) / BOX_LERP_MS);
      const current = lerpBbox(existing.from, existing.to, progress);
      return {
        ...track,
        from: current,
        to: bbox,
        updatedAt: now,
      };
    });

    overlayRef.current = {
      tracks: nextTracks,
      line: data.line ?? null,
      frameWidth: data.frame_width ?? 0,
      frameHeight: data.frame_height ?? 0,
      totalCount: data.total_count ?? 0,
    };
    setHasProcessorOverlay(true);
  }, []);

  const assertCameraSupported = useCallback(() => {
    if (!window.isSecureContext) {
      throw new Error(
        "A câmera só funciona em HTTPS ou em http://localhost. Abra http://localhost:8009/contagem"
      );
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("Seu navegador não suporta acesso à câmera.");
    }
  }, []);

  const loadCameras = useCallback(async (requestPermission = false): Promise<CameraDevice[]> => {
    if (!window.isSecureContext || !navigator.mediaDevices?.enumerateDevices) {
      return [];
    }

    setLoadingCameras(true);
    try {
      if (requestPermission) {
        const temp = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        temp.getTracks().forEach((track) => track.stop());
      }

      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = devices
        .filter((device) => device.kind === "videoinput")
        .map((device, index) => ({
          deviceId: device.deviceId,
          label: device.label.trim() || `Câmera ${index + 1}`,
        }));

      setCameras(videoInputs);
      setSelectedCameraId((current) => {
        if (current && videoInputs.some((camera) => camera.deviceId === current)) {
          return current;
        }
        return videoInputs[0]?.deviceId ?? "";
      });
      return videoInputs;
    } catch (e) {
      if (requestPermission) {
        setError(e instanceof Error ? e.message : "Falha ao listar câmeras");
      }
      return [];
    } finally {
      setLoadingCameras(false);
    }
  }, []);

  const attachStreamToVideo = useCallback(async (stream: MediaStream) => {
    const video = videoRef.current;
    if (!video) {
      throw new Error("Elemento de vídeo indisponível.");
    }

    video.srcObject = stream;
    await new Promise<void>((resolve, reject) => {
      const onReady = () => {
        video.removeEventListener("loadedmetadata", onReady);
        video.removeEventListener("error", onError);
        resolve();
      };
      const onError = () => {
        video.removeEventListener("loadedmetadata", onReady);
        video.removeEventListener("error", onError);
        reject(new Error("Falha ao carregar o vídeo da câmera."));
      };
      if (video.readyState >= 1) {
        resolve();
        return;
      }
      video.addEventListener("loadedmetadata", onReady);
      video.addEventListener("error", onError);
    });
    await video.play();
    setCameraReady(true);
  }, []);

  const refreshStatus = useCallback(async () => {
    try {
      const data = await fetchContagemStatus();
      setStatus(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao obter status");
    }
  }, []);

  useEffect(() => {
    void refreshStatus();
    void loadCameras();
    setCompletedDailyTotal(readDailyTotal());
    const storedGranja = readStoredGranja();
    setSelectedGranja(
      GRANJA_OPTIONS.includes(storedGranja as (typeof GRANJA_OPTIONS)[number])
        ? (storedGranja as (typeof GRANJA_OPTIONS)[number])
        : GRANJA_OPTIONS[0]
    );
    const storedLote = readStoredLote();
    setLoteDigits(storedLote.digits);
    setLoteSiglas(storedLote.siglas);
  }, [loadCameras, refreshStatus]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      const current = new Date();
      setNow(current);
      setCompletedDailyTotal((prev) => {
        const stored = readDailyTotal();
        return stored === prev ? prev : stored;
      });
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const accumulateSessionCount = useCallback((sessionTotal: number) => {
    if (sessionTotal <= 0) return;

    setCompletedDailyTotal((prev) => {
      const next = prev + sessionTotal;
      writeDailyTotal(next);
      return next;
    });
  }, []);

  useEffect(() => {
    if (!navigator.mediaDevices?.addEventListener) return;

    const onDeviceChange = () => {
      void loadCameras();
    };

    navigator.mediaDevices.addEventListener("devicechange", onDeviceChange);
    return () => navigator.mediaDevices.removeEventListener("devicechange", onDeviceChange);
  }, [loadCameras]);

  const openCameraStream = useCallback(async (deviceId: string, cameraLabel: string) => {
    const attempts: MediaTrackConstraints[] = deviceId
      ? [
          { deviceId: { exact: deviceId } },
          {
            deviceId: { exact: deviceId },
            width: { ideal: 960 },
            height: { ideal: 540 },
          },
          {
            deviceId: { exact: deviceId },
            width: { ideal: 848 },
            height: { ideal: 478 },
          },
          {
            deviceId: { exact: deviceId },
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          { deviceId: { ideal: deviceId } },
        ]
      : [
          { width: { ideal: 960 }, height: { ideal: 540 } },
          { width: { ideal: 848 }, height: { ideal: 478 } },
        ];

    let lastMismatchLabel = "";
    let lastError: unknown;

    for (const video of attempts) {
      let stream: MediaStream | null = null;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: false, video });
        const [track] = stream.getVideoTracks();
        const openedDeviceId = track?.getSettings().deviceId;

        if (deviceId && openedDeviceId && openedDeviceId !== deviceId) {
          lastMismatchLabel = track?.label || "outra câmera";
          track?.stop();
          continue;
        }

        return stream;
      } catch (error) {
        stream?.getTracks().forEach((track) => track.stop());
        lastError = error;
        if (error instanceof DOMException && error.name === "OverconstrainedError") {
          continue;
        }
        throw error;
      }
    }

    if (lastMismatchLabel) {
      throw new Error(
        `O navegador abriu "${lastMismatchLabel}" em vez de "${cameraLabel}". Feche o DroidCam no PC/celular, clique em Parar e teste novamente.`
      );
    }

    throw lastError instanceof Error
      ? lastError
      : new Error(`Não foi possível abrir "${cameraLabel}". Verifique se ela não está em uso.`);
  }, []);

  const updateStreamInfo = useCallback((stream: MediaStream) => {
    const [track] = stream.getVideoTracks();
    if (!track) {
      setStreamInfo(null);
      return;
    }
    const settings = track.getSettings();
    const resolution =
      settings.width && settings.height ? `${settings.width}×${settings.height}` : "resolução desconhecida";
    setStreamInfo(`${track.label || "Câmera"} · ${resolution}`);
  }, []);

  const evaluateFeedQuality = useCallback((cameraLabel: string) => {
    const canvas = previewCanvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx || canvas.width === 0 || canvas.height === 0) return;

    if (!isLikelyBlankFeed(ctx, canvas.width, canvas.height)) {
      setSourceWarning(null);
      return;
    }

    if (/droidcam/i.test(cameraLabel)) {
      setSourceWarning(
        "DroidCam conectado, mas sem imagem. Abra o app DroidCam no celular, inicie a câmera e aguarde alguns segundos antes de testar novamente."
      );
      return;
    }

    setSourceWarning(
      "A câmera abriu, mas o frame está vazio ou uniforme. Verifique se a fonte está ativa e tente outra câmera."
    );
  }, []);

  const clearPreviewSurfaces = useCallback(() => {
    setHasProcessorOverlay(false);
    setSourceWarning(null);
    overlayRef.current = {
      tracks: [],
      line: null,
      frameWidth: 0,
      frameHeight: 0,
      totalCount: 0,
    };

    for (const canvas of [
      previewCanvasRef.current,
      processorCanvasRef.current,
      captureCanvasRef.current,
    ]) {
      if (!canvas) continue;
      const ctx = canvas.getContext("2d");
      if (!ctx) continue;
      ctx.clearRect(0, 0, canvas.width || 1, canvas.height || 1);
    }
  }, []);

  const stopCountingLoop = useCallback(() => {
    countingLoopActiveRef.current = false;
    frameProcessingRef.current = false;
    pendingFrameRef.current = null;
    if (loopRef.current !== null) {
      cancelAnimationFrame(loopRef.current);
      loopRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.playbackRate = 1;
    }
  }, []);

  const stopFrameLoops = useCallback(() => {
    stopCountingLoop();
    if (previewLoopRef.current) {
      window.cancelAnimationFrame(previewLoopRef.current);
      previewLoopRef.current = null;
    }
  }, [stopCountingLoop]);

  const stopPlayback = useCallback(() => {
    stopFrameLoops();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    activeDeviceIdRef.current = null;
    setActiveDeviceId(null);
    if (fileUrlRef.current) {
      URL.revokeObjectURL(fileUrlRef.current);
      fileUrlRef.current = null;
    }
    const video = videoRef.current;
    if (video) {
      video.onended = null;
      video.pause();
      video.playbackRate = 1;
      video.removeAttribute("src");
      video.srcObject = null;
      video.load();
    }
    setRunning(false);
    setPaused(false);
    setPreviewOnly(false);
    setVideoFileName(null);
    setVideoDuration(0);
    setVideoCurrentTime(0);
    setCameraReady(false);
    setStreamInfo(null);
    setPipelineReady(false);
    setPreparingPipeline(false);
    sessionPreparedRef.current = false;
    clearPreviewSurfaces();
  }, [clearPreviewSurfaces, stopFrameLoops]);

  const drawLocalPreview = useCallback(() => {
    const video = videoRef.current;
    const liveCanvas = previewCanvasRef.current;
    const processorCanvas = processorCanvasRef.current;
    if (!video || !liveCanvas || video.readyState < 2) return false;

    const width = video.videoWidth;
    const height = video.videoHeight;
    if (!width || !height) return false;

    const drawVideo = (canvas: HTMLCanvasElement) => {
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
      const ctx = canvas.getContext("2d");
      if (!ctx) return null;
      ctx.drawImage(video, 0, 0, width, height);
      return ctx;
    };

    if (!drawVideo(liveCanvas)) return false;

    if (processorCanvas) {
      const ctx = drawVideo(processorCanvas);
      if (ctx) {
        const overlay = overlayRef.current;
        const sx = overlay.frameWidth > 0 ? width / overlay.frameWidth : 1;
        const sy = overlay.frameHeight > 0 ? height / overlay.frameHeight : 1;

        if (overlay.line) {
          ctx.strokeStyle = "#ff8000";
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(overlay.line.x1 * sx, overlay.line.y1 * sy);
          ctx.lineTo(overlay.line.x2 * sx, overlay.line.y2 * sy);
          ctx.stroke();
        }

        for (const track of overlay.tracks) {
          const progress = Math.min(1, (performance.now() - track.updatedAt) / BOX_LERP_MS);
          const [x1, y1, x2, y2] = lerpBbox(track.from, track.to, progress);
          const px1 = x1 * sx;
          const py1 = y1 * sy;
          const px2 = x2 * sx;
          const py2 = y2 * sy;
          ctx.strokeStyle = "#ef4444";
          ctx.lineWidth = 2.5;
          ctx.strokeRect(px1, py1, px2 - px1, py2 - py1);
          ctx.fillStyle = "#ef4444";
          ctx.font = "bold 13px sans-serif";
          ctx.fillText(`egg #${track.track_id}`, px1, Math.max(14, py1 - 6));
        }

        if (overlay.totalCount > 0 || overlay.tracks.length > 0) {
          const label = `TOTAL: ${overlay.totalCount}`;
          ctx.font = "bold 20px sans-serif";
          ctx.fillStyle = "rgba(15, 23, 42, 0.7)";
          const metrics = ctx.measureText(label);
          const padX = 10;
          const padY = 8;
          const boxW = metrics.width + padX * 2;
          const boxH = 28 + padY;
          ctx.fillRect(12, 12, boxW, boxH);
          ctx.fillStyle = "#f8fafc";
          ctx.fillText(label, 12 + padX, 12 + boxH - padY - 2);
        }
      }
    }
    return true;
  }, []);

  const handleVideoEnded = useCallback(async () => {
    stopFrameLoops();
    const video = videoRef.current;
    if (video) {
      video.onended = null;
      video.pause();
    }
    drawLocalPreview();
    setRunning(false);
    setPaused(false);
    setPreviewOnly(false);
    setPipelineReady(false);
    sessionPreparedRef.current = false;
    try {
      const data = await pararContagem();
      setStatus(data);
      accumulateSessionCount(data.total_count);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao parar");
    }
  }, [accumulateSessionCount, drawLocalPreview, stopFrameLoops]);

  const startPreviewLoop = useCallback(() => {
    const tick = () => {
      drawLocalPreview();
      previewLoopRef.current = window.requestAnimationFrame(tick);
    };
    previewLoopRef.current = window.requestAnimationFrame(tick);
  }, [drawLocalPreview]);

  const startFrameLoop = useCallback(() => {
    let sessionRecovering = false;

    const sendFrame = async (imageB64: string, capturedVideoTime: number) => {
      frameProcessingRef.current = true;
      const video = videoRef.current;
      const isUploadedVideo = Boolean(videoFileNameRef.current);
      const startedAt = performance.now();

      // Com ensemble (2 modelos), o processamento e mais lento: segura o video.
      if (isUploadedVideo && video && !video.paused && !video.ended) {
        video.playbackRate = 0.45;
      }

      try {
        const data = await enviarFrameBase64(imageB64);
        if (data.skipped) {
          // Sessao idle — tenta recuperar uma vez sem poluir a UI com 409.
          if (countingLoopActiveRef.current && !sessionRecovering) {
            sessionRecovering = true;
            try {
              await iniciarContagem(
                videoFileNameRef.current ? "uploaded_video" : "browser_camera"
              );
              const retry = await enviarFrameBase64(imageB64);
              if (!retry.skipped) {
                lastFrameSentAtRef.current = performance.now();
                lastProcessedVideoTimeRef.current = capturedVideoTime;
                setStatus(retry);
                updateProcessorOverlay(retry);
              }
            } catch {
              /* ignore recover race */
            } finally {
              sessionRecovering = false;
            }
          }
          return;
        }

        lastFrameSentAtRef.current = performance.now();
        lastProcessedVideoTimeRef.current = capturedVideoTime;
        setStatus(data);
        updateProcessorOverlay(data);

        if (isUploadedVideo && video) {
          const elapsed = performance.now() - startedAt;
          const lag = video.currentTime - lastProcessedVideoTimeRef.current;
          // Sincroniza taxa de play com tempo real do processador
          const targetRate = Math.min(1, Math.max(0.35, 280 / Math.max(180, elapsed)));
          video.playbackRate = lag > 0.35 ? Math.min(targetRate, 0.5) : targetRate;
        }
      } catch (e) {
        const message = e instanceof Error ? e.message : "Falha ao enviar frame";
        const isConflict = /409|sessao|sessão|skipped/i.test(message);
        if (isConflict) {
          if (countingLoopActiveRef.current && !sessionRecovering) {
            sessionRecovering = true;
            try {
              await iniciarContagem(
                videoFileNameRef.current ? "uploaded_video" : "browser_camera"
              );
            } catch {
              /* ignore */
            } finally {
              sessionRecovering = false;
            }
          }
          // Nao mostra erro vermelho de 409 — e corrida de sessao, nao falha fatal.
          return;
        }
        setError(message);
      } finally {
        frameProcessingRef.current = false;
        const pending = pendingFrameRef.current;
        pendingFrameRef.current = null;
        if (pending && countingLoopActiveRef.current) {
          void sendFrame(pending.imageB64, pending.videoTime);
        } else if (isUploadedVideo && video && countingLoopActiveRef.current && !video.ended) {
          // Restaura ritmo quando a fila esvazia
          if (video.playbackRate < 0.85) {
            video.playbackRate = Math.min(1, video.playbackRate + 0.15);
          }
        }
      }
    };

    const runCountingLoop = async () => {
      if (!countingLoopActiveRef.current) return;

      const video = videoRef.current;
      const canvas = captureCanvasRef.current;
      if (!video || !canvas || video.readyState < 2) {
        loopRef.current = requestAnimationFrame(() => void runCountingLoop());
        return;
      }

      if (video.ended) {
        void handleVideoEnded();
        return;
      }

      const now = performance.now();
      const isUploadedVideo = Boolean(videoFileNameRef.current);

      // Enquanto processa, nao captura novos frames do video — evita backlog/409.
      if (frameProcessingRef.current) {
        if (isUploadedVideo && !video.paused && !video.ended) {
          video.playbackRate = Math.min(video.playbackRate, 0.4);
        }
        loopRef.current = requestAnimationFrame(() => void runCountingLoop());
        return;
      }

      if (isUploadedVideo) {
        const videoDelta = video.currentTime - lastProcessedVideoTimeRef.current;
        if (videoDelta < VIDEO_SAMPLE_SECONDS && lastProcessedVideoTimeRef.current > 0) {
          loopRef.current = requestAnimationFrame(() => void runCountingLoop());
          return;
        }
      } else if (now - lastFrameSentAtRef.current < MIN_FRAME_INTERVAL_MS) {
        loopRef.current = requestAnimationFrame(() => void runCountingLoop());
        return;
      }

      const capturedVideoTime = video.currentTime;
      const imageB64 = captureFrameBase64(video, canvas);
      if (!imageB64) {
        loopRef.current = requestAnimationFrame(() => void runCountingLoop());
        return;
      }

      await sendFrame(imageB64, capturedVideoTime);
      if (countingLoopActiveRef.current) {
        loopRef.current = requestAnimationFrame(() => void runCountingLoop());
      }
    };

    countingLoopActiveRef.current = true;
    frameProcessingRef.current = false;
    pendingFrameRef.current = null;
    lastFrameSentAtRef.current = 0;
    lastProcessedVideoTimeRef.current = 0;
    loopRef.current = requestAnimationFrame(() => void runCountingLoop());
  }, [handleVideoEnded, updateProcessorOverlay]);

  const connectCamera = useCallback(
    async (deviceId: string, cameraLabel: string) => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;

      const stream = await openCameraStream(deviceId, cameraLabel);
      const [track] = stream.getVideoTracks();
      const openedDeviceId = track?.getSettings().deviceId ?? deviceId;
      const openedLabel = track?.label || cameraLabel;

      streamRef.current = stream;
      activeDeviceIdRef.current = openedDeviceId;
      setActiveDeviceId(openedDeviceId);
      await attachStreamToVideo(stream);

      const video = videoRef.current;
      if (!video) {
        throw new Error("Elemento de vídeo indisponível.");
      }

      await waitForVideoDimensions(video);
      updateStreamInfo(stream);
      drawLocalPreview();
      startPreviewLoop();

      await wait(800);
      drawLocalPreview();
      evaluateFeedQuality(openedLabel);
    },
    [attachStreamToVideo, drawLocalPreview, evaluateFeedQuality, openCameraStream, startPreviewLoop, updateStreamInfo]
  );

  const handleCameraSelection = useCallback(
    (nextDeviceId: string) => {
      setSelectedCameraId(nextDeviceId);
      if (activeDeviceIdRef.current && activeDeviceIdRef.current !== nextDeviceId) {
        stopPlayback();
      }
    },
    [stopPlayback]
  );

  const resolveDeviceId = useCallback(async () => {
    const available = await loadCameras(false);
    let deviceId = selectedCameraId;

    if (deviceId && !available.some((camera) => camera.deviceId === deviceId)) {
      const previous = cameras.find((camera) => camera.deviceId === selectedCameraId);
      const byLabel = previous
        ? available.find((camera) => camera.label === previous.label)
        : undefined;
      deviceId = byLabel?.deviceId ?? "";
    }

    if (!deviceId) {
      deviceId = available[0]?.deviceId ?? "";
    }
    if (!deviceId) {
      const refreshed = await loadCameras(true);
      deviceId = refreshed[0]?.deviceId ?? "";
    }
    if (!deviceId) {
      throw new Error("Nenhuma câmera disponível. Clique em Atualizar câmeras e permita o acesso.");
    }
    return deviceId;
  }, [cameras, loadCameras, selectedCameraId]);

  const testCamera = useCallback(async () => {
    setError(null);
    setSourceWarning(null);
    setLoading(true);
    setPreviewOnly(false);
    stopPlayback();

    try {
      assertCameraSupported();
      await loadCameras(false);
      const deviceId = await resolveDeviceId();
      const cameraLabel =
        cameras.find((camera) => camera.deviceId === deviceId)?.label ??
        (await loadCameras(false)).find((camera) => camera.deviceId === deviceId)?.label ??
        "";
      await connectCamera(deviceId, cameraLabel);
      setPreviewOnly(true);
      void loadCameras();
    } catch (e) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      setCameraReady(false);
      setStreamInfo(null);

      if (e instanceof DOMException) {
        if (e.name === "NotAllowedError" || e.name === "PermissionDeniedError") {
          setError("Permissão da câmera negada. Autorize o acesso no navegador e tente novamente.");
          return;
        }
        if (e.name === "NotFoundError" || e.name === "DevicesNotFoundError") {
          setError("Nenhuma câmera foi encontrada neste dispositivo.");
          return;
        }
        if (e.name === "NotReadableError") {
          setError("A câmera está em uso por outro aplicativo.");
          return;
        }
      }

      setError(e instanceof Error ? e.message : "Falha ao testar a câmera");
    } finally {
      setLoading(false);
    }
  }, [assertCameraSupported, cameras, connectCamera, loadCameras, resolveDeviceId, stopPlayback]);

  const startCamera = useCallback(async () => {
    setError(null);
    setSourceWarning(null);
    setLoading(true);
    setCameraReady(false);
    stopPlayback();

    try {
      assertCameraSupported();
      await loadCameras(false);
      const deviceId = await resolveDeviceId();
      const cameraLabel =
        cameras.find((camera) => camera.deviceId === deviceId)?.label ??
        (await loadCameras(false)).find((camera) => camera.deviceId === deviceId)?.label ??
        "";
      await connectCamera(deviceId, cameraLabel);
      void loadCameras();

      await iniciarContagem("browser_camera");
      sessionStartedAtRef.current = new Date();
      setPreviewOnly(false);
      setPaused(false);
      setRunning(true);
      startPreviewLoop();
      startFrameLoop();
    } catch (e) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      const video = videoRef.current;
      if (video) {
        video.srcObject = null;
      }
      setCameraReady(false);
      setRunning(false);

      if (e instanceof DOMException) {
        if (e.name === "NotAllowedError" || e.name === "PermissionDeniedError") {
          setError("Permissão da câmera negada. Autorize o acesso no navegador e tente novamente.");
          return;
        }
        if (e.name === "NotFoundError" || e.name === "DevicesNotFoundError") {
          setError("Nenhuma câmera foi encontrada neste dispositivo.");
          return;
        }
        if (e.name === "NotReadableError") {
          setError("A câmera está em uso por outro aplicativo.");
          return;
        }
      }

      setError(e instanceof Error ? e.message : "Falha ao iniciar a câmera");
    } finally {
      setLoading(false);
    }
  }, [
    assertCameraSupported,
    cameras,
    connectCamera,
    loadCameras,
    resolveDeviceId,
    startFrameLoop,
    startPreviewLoop,
    stopPlayback,
  ]);

  const prepareVideoPipeline = useCallback(async () => {
    const video = videoRef.current;
    const canvas = captureCanvasRef.current;
    if (!video || !canvas) {
      throw new Error("Elemento de vídeo indisponível para preparar a contagem.");
    }

    setPreparingPipeline(true);
    setPipelineReady(false);
    sessionPreparedRef.current = false;
    setError(null);

    try {
      stopCountingLoop();
      video.pause();
      await seekVideoTo(video, 0);
      drawLocalPreview();

      await iniciarContagem("uploaded_video");
      sessionStartedAtRef.current = new Date();

      const imageB64 = captureFrameBase64(video, canvas);
      if (!imageB64) {
        throw new Error("Não foi possível capturar o frame inicial do vídeo.");
      }

      const data = await enviarFrameBase64(imageB64);
      setStatus(data);
      updateProcessorOverlay(data);

      if (!data.line) {
        throw new Error("Processador não retornou a linha de contagem.");
      }

      lastProcessedVideoTimeRef.current = video.currentTime;
      lastFrameSentAtRef.current = performance.now();
      sessionPreparedRef.current = true;
      setPipelineReady(true);
      drawLocalPreview();
      return data;
    } catch (e) {
      sessionPreparedRef.current = false;
      setPipelineReady(false);
      try {
        await pararContagem();
      } catch {
        /* ignore */
      }
      throw e;
    } finally {
      setPreparingPipeline(false);
    }
  }, [drawLocalPreview, stopCountingLoop, updateProcessorOverlay]);

  const startVideoFile = useCallback(
    async (file: File) => {
      setError(null);
      setLoading(true);
      setPipelineReady(false);

      const hadSession = sessionPreparedRef.current || running || paused;
      sessionPreparedRef.current = false;
      if (hadSession) {
        try {
          await pararContagem();
        } catch {
          /* ignore */
        }
      }
      stopPlayback();

      try {
        const url = URL.createObjectURL(file);
        fileUrlRef.current = url;
        setVideoFileName(file.name);

        const video = videoRef.current;
        if (!video) return;

        video.srcObject = null;
        video.src = url;
        video.loop = false;
        video.muted = true;
        video.onended = () => {
          void handleVideoEnded();
        };

        await new Promise<void>((resolve, reject) => {
          const onReady = () => {
            video.removeEventListener("loadeddata", onReady);
            video.removeEventListener("error", onError);
            resolve();
          };
          const onError = () => {
            video.removeEventListener("loadeddata", onReady);
            video.removeEventListener("error", onError);
            reject(new Error("Falha ao carregar o vídeo."));
          };
          if (video.readyState >= 2) {
            resolve();
            return;
          }
          video.addEventListener("loadeddata", onReady);
          video.addEventListener("error", onError);
        });

        video.pause();
        await seekVideoTo(video, 0);
        setCameraReady(true);
        setPreviewOnly(true);
        setRunning(false);
        setPaused(false);
        drawLocalPreview();
        startPreviewLoop();

        setLoading(false);
        await prepareVideoPipeline();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Falha ao carregar o vídeo");
        setPipelineReady(false);
        sessionPreparedRef.current = false;
        stopPlayback();
      } finally {
        setLoading(false);
        setPreparingPipeline(false);
      }
    },
    [
      drawLocalPreview,
      handleVideoEnded,
      paused,
      prepareVideoPipeline,
      running,
      startPreviewLoop,
      stopPlayback,
    ]
  );

  const clearOverlayTracks = useCallback(() => {
    overlayRef.current = {
      ...overlayRef.current,
      tracks: [],
      totalCount: overlayRef.current.totalCount,
    };
  }, []);

  const handleStop = useCallback(async () => {
    const wasCounting = running;
    const hadPreparedSession = sessionPreparedRef.current || pipelineReady;
    clearOverlayTracks();
    setHasProcessorOverlay(false);
    setPipelineReady(false);
    sessionPreparedRef.current = false;
    stopPlayback();
    setPaused(false);
    if (!wasCounting && !hadPreparedSession) return;

    try {
      const data = await pararContagem();
      setStatus(data);
      accumulateSessionCount(data.total_count);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao parar");
    }
  }, [accumulateSessionCount, clearOverlayTracks, pipelineReady, running, stopPlayback]);

  const handlePause = useCallback(() => {
    stopCountingLoop();
    videoRef.current?.pause();
    clearOverlayTracks();
    setPaused(true);
  }, [clearOverlayTracks, stopCountingLoop]);

  const handleResume = useCallback(async () => {
    const video = videoRef.current;
    if (!video) return;

    setError(null);
    setLoading(true);

    try {
      if (!running && previewOnly && videoFileName) {
        if (!sessionPreparedRef.current || !pipelineReady) {
          await prepareVideoPipeline();
        }
        await video.play();
        setPreviewOnly(false);
        setPaused(false);
        setRunning(true);
        startPreviewLoop();
        startFrameLoop();
        return;
      }

      if (running && paused) {
        await video.play();
        setPaused(false);
        startPreviewLoop();
        startFrameLoop();
      }
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : !running && previewOnly
            ? "Falha ao iniciar a contagem"
            : "Falha ao retomar a contagem"
      );
    } finally {
      setLoading(false);
    }
  }, [
    paused,
    pipelineReady,
    prepareVideoPipeline,
    previewOnly,
    running,
    startFrameLoop,
    startPreviewLoop,
    videoFileName,
  ]);

  const handleRestartVideo = useCallback(async () => {
    const video = videoRef.current;
    if (!video || !videoFileName) return;

    setError(null);
    setLoading(true);
    stopCountingLoop();

    try {
      if (running || paused || sessionPreparedRef.current) {
        try {
          const data = await pararContagem();
          setStatus(data);
          if (running || paused) {
            accumulateSessionCount(data.total_count);
          }
        } catch {
          /* sessao pode ja estar encerrada */
        }
      }

      overlayRef.current = {
        tracks: [],
        line: null,
        frameWidth: 0,
        frameHeight: 0,
        totalCount: 0,
      };
      setHasProcessorOverlay(false);
      setPipelineReady(false);
      sessionPreparedRef.current = false;

      video.onended = () => {
        void handleVideoEnded();
      };
      video.playbackRate = 1;
      video.pause();
      setPreviewOnly(true);
      setRunning(false);
      setPaused(false);
      startPreviewLoop();

      setLoading(false);
      await prepareVideoPipeline();

      await video.play();
      setPreviewOnly(false);
      setPaused(false);
      setRunning(true);
      startPreviewLoop();
      startFrameLoop();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao reiniciar o video");
      setRunning(false);
      setPaused(false);
      setPreviewOnly(true);
      setPipelineReady(false);
      sessionPreparedRef.current = false;
      video.pause();
      video.currentTime = 0;
      drawLocalPreview();
    } finally {
      setLoading(false);
      setPreparingPipeline(false);
    }
  }, [
    accumulateSessionCount,
    drawLocalPreview,
    handleVideoEnded,
    paused,
    prepareVideoPipeline,
    running,
    startFrameLoop,
    startPreviewLoop,
    stopCountingLoop,
    videoFileName,
  ]);

  const handleGenerateReport = useCallback(async () => {
    setError(null);
    setReportLoading(true);
    try {
      const endedAt = new Date();
      const startedAt = sessionStartedAtRef.current ?? endedAt;
      const lote = `${loteDigits}-${loteSiglas}`;
      const sessionTotal = status?.total_count ?? 0;
      await generateContagemReportPdf({
        granja: selectedGranja,
        lote,
        totalOvos: sessionTotal,
        startedAt,
        endedAt,
        videoName: videoFileName,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao gerar o relatorio PDF");
    } finally {
      setReportLoading(false);
    }
  }, [loteDigits, loteSiglas, selectedGranja, status?.total_count, videoFileName]);

  const selectedCameraLabel =
    cameras.find((camera) => camera.deviceId === selectedCameraId)?.label ?? "—";
  const hasSelectionMismatch =
    Boolean(activeDeviceId && selectedCameraId && activeDeviceId !== selectedCameraId);
  const isOn = running && !paused;
  const totalOvos = status?.total_count ?? 0;
  const activeSessionCount = running || paused ? totalOvos : 0;
  const dailyTotal = completedDailyTotal + activeSessionCount;
  const awaitingVideoStart = Boolean(previewOnly && videoFileName && cameraReady && !running);
  const canResumeCounting =
    (running && paused) || (awaitingVideoStart && pipelineReady && !preparingPipeline);
  const canRestartVideo = Boolean(
    videoFileName && cameraReady && !loading && !preparingPipeline
  );

  useEffect(() => () => stopPlayback(), [stopPlayback]);

  useEffect(() => {
    if (!menuOpen) return;

    const onPointerDown = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };

    window.addEventListener("mousedown", onPointerDown);
    return () => window.removeEventListener("mousedown", onPointerDown);
  }, [menuOpen]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !videoFileName) {
      setVideoDuration(0);
      setVideoCurrentTime(0);
      return;
    }

    const syncDuration = () => {
      setVideoDuration(Number.isFinite(video.duration) ? video.duration : 0);
    };
    const syncCurrentTime = () => {
      setVideoCurrentTime(video.currentTime);
    };

    video.addEventListener("loadedmetadata", syncDuration);
    video.addEventListener("durationchange", syncDuration);
    video.addEventListener("timeupdate", syncCurrentTime);
    syncDuration();
    syncCurrentTime();

    return () => {
      video.removeEventListener("loadedmetadata", syncDuration);
      video.removeEventListener("durationchange", syncDuration);
      video.removeEventListener("timeupdate", syncCurrentTime);
    };
  }, [videoFileName, cameraReady]);

  const handleGranjaChange = useCallback((value: string) => {
    setSelectedGranja(value);
    localStorage.setItem(GRANJA_STORAGE_KEY, value);
  }, []);

  const handleLoteDigitsChange = useCallback((value: string) => {
    setLoteDigits(value.replace(/\D/g, "").slice(0, 4));
  }, []);

  const handleLoteSiglasChange = useCallback((value: string) => {
    setLoteSiglas(value.replace(/[^a-zA-Z]/g, "").slice(0, 2).toUpperCase());
  }, []);

  const persistLote = useCallback((digits: string, siglas: string) => {
    const normalizedDigits = digits.padStart(4, "0").slice(-4);
    const normalizedSiglas = siglas.padEnd(2, "A").slice(0, 2).toUpperCase();
    setLoteDigits(normalizedDigits);
    setLoteSiglas(normalizedSiglas);
    writeStoredLote(normalizedDigits, normalizedSiglas);
  }, []);

  return (
    <div className="contador-shell mx-auto flex h-dvh max-h-dvh w-full max-w-7xl flex-col gap-1.5 overflow-hidden px-3 py-2 md:px-4">
      <header className="contador-header relative z-50 shrink-0 overflow-visible rounded-lg pb-1.5 pt-1.5">
        <div
          aria-hidden
          className="contador-header-glow pointer-events-none absolute inset-x-0 bottom-0 h-px opacity-60"
        />

        <div className="relative flex items-center gap-2 px-2">
          <div className="flex shrink-0 items-stretch gap-1.5">
            <DateTimeCard dateTime={now} />

            <div ref={menuRef} className="relative z-50">
              <button
                type="button"
                onClick={() => setMenuOpen((open) => !open)}
                className={`menu-trigger flex h-full min-h-[52px] flex-col items-center justify-center gap-0.5 px-2.5 ${menuOpen ? "menu-trigger-open" : ""}`}
              >
                <Menu className="h-4 w-4 text-[var(--rovah-green)]" strokeWidth={1.75} />
                <span className="text-[9px] font-bold uppercase tracking-wide">
                  Menu
                </span>
                <ChevronDown
                  className={`h-3 w-3 opacity-70 transition ${menuOpen ? "rotate-180" : ""}`}
                  strokeWidth={1.75}
                />
              </button>

              {menuOpen && (
                <div className="menu-panel absolute left-0 top-[calc(100%+4px)] z-[100] w-64 p-2">
                  <label className="mb-1.5 flex flex-col gap-1 rounded-md border border-[var(--rovah-border)] bg-[var(--rovah-bg)] p-2">
                    <span className="menu-panel-label flex items-center gap-1.5">
                      <Camera className="h-3.5 w-3.5 text-[var(--rovah-green-dark)]" strokeWidth={1.75} />
                      Câmera
                    </span>
                    <select
                      className="info-card-field rounded-md px-2 py-1 text-xs"
                      value={selectedCameraId}
                      disabled={running || loading || loadingCameras || cameras.length === 0}
                      onChange={(e) => handleCameraSelection(e.target.value)}
                    >
                      {cameras.length === 0 ? (
                        <option value="">Nenhuma câmera</option>
                      ) : (
                        cameras.map((camera) => (
                          <option key={camera.deviceId} value={camera.deviceId}>
                            {camera.label}
                          </option>
                        ))
                      )}
                    </select>
                  </label>

                  <div className="space-y-0.5">
                    <MenuItem
                      icon={<RefreshCw className="h-4 w-4" strokeWidth={1.75} />}
                      label={loadingCameras ? "Listando…" : "Atualizar câmeras"}
                      disabled={running || loading || loadingCameras}
                      onClick={() => void loadCameras(true)}
                    />
                    <MenuItem
                      icon={<Video className="h-4 w-4" strokeWidth={1.75} />}
                      label={loading && previewOnly ? "Testando…" : "Testar câmera"}
                      disabled={running || loading || cameras.length === 0}
                      onClick={() => void testCamera()}
                    />
                    <MenuItem
                      icon={<PlayCircle className="h-4 w-4" strokeWidth={1.75} />}
                      label={loading ? "Iniciando…" : "Iniciar câmera"}
                      tone="success"
                      disabled={running || loading || cameras.length === 0}
                      onClick={() => void startCamera()}
                    />
                    <MenuItem
                      icon={<FileVideo className="h-4 w-4" strokeWidth={1.75} />}
                      label={loading ? "Carregando…" : "Adicionar vídeo"}
                      tone="primary"
                      disabled={running || loading}
                      onClick={() => fileInputRef.current?.click()}
                    />
                  </div>
                </div>
              )}

              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    setMenuOpen(false);
                    void startVideoFile(file);
                  }
                  e.target.value = "";
                }}
              />
            </div>
          </div>

          <div className="flex min-w-0 flex-1 flex-col items-center gap-0.5 px-1">
            <div className="flex items-center gap-1.5">
              <ScanEye className="h-4 w-4 shrink-0 text-[var(--rovah-green)]" strokeWidth={1.75} />
              <span className="contador-subtitle text-[9px] font-semibold uppercase sm:text-[10px]">
                Egg Vision AI
              </span>
              <ScanEye className="h-4 w-4 shrink-0 text-[var(--rovah-green)]" strokeWidth={1.75} />
            </div>
            <h1 className="contador-title text-center text-2xl font-extrabold md:text-3xl">
              CONTADOR DE OVOS
            </h1>
          </div>

          <Image
            src="/logo-bica-meu-galo.png"
            alt="Bica Meu Galo"
            width={96}
            height={96}
            className="shrink-0 rounded-full border-2 border-[var(--rovah-green)] bg-white shadow-md"
            priority
          />
        </div>
      </header>

      {error && (
        <div className="shrink-0 rounded-md border border-rose-200 bg-rose-50 px-2 py-1 text-center text-xs text-rose-700">
          {error}
        </div>
      )}

      {(cameras.length > 0 && cameras.every((camera) => camera.label.startsWith("Câmera "))) ||
      hasSelectionMismatch ||
      videoFileName ? (
        <section className="shrink-0 rounded-md border border-[var(--rovah-border)] bg-white px-2 py-1 text-center text-[11px] text-[var(--rovah-text-muted)] shadow-sm">
          {videoFileName && (
            <p>
              Vídeo: <span className="font-semibold text-[var(--rovah-text)]">{videoFileName}</span>
            </p>
          )}
          {hasSelectionMismatch && (
            <p className="text-amber-700">
              Selecionada: {selectedCameraLabel}. Clique em &quot;Testar câmera&quot; para trocar.
            </p>
          )}
          {cameras.length > 0 && cameras.every((camera) => camera.label.startsWith("Câmera ")) && (
            <p>Atualize as câmeras para ver os nomes corretos.</p>
          )}
        </section>
      ) : null}

      {sourceWarning && (
        <div className="shrink-0 rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-center text-[11px] text-amber-800">
          {sourceWarning}
        </div>
      )}

      <section className="relative z-0 flex min-h-0 flex-1 flex-col gap-1">
        <div className="relative min-h-0 flex-1">
          <div className="grid h-full min-h-0 grid-cols-1 gap-2 md:grid-cols-2">
            <div className="relative flex min-h-0 flex-col overflow-hidden rounded-lg border border-[var(--rovah-border)] bg-white shadow-sm">
              <p className="panel-heading shrink-0 px-2 py-0.5 text-center">
                Ao vivo
              </p>
              <div className="relative min-h-0 flex-1 bg-slate-950">
                <video ref={videoRef} className="hidden" autoPlay muted playsInline />
                <canvas ref={previewCanvasRef} className="h-full w-full object-contain" />
                <canvas ref={captureCanvasRef} className="hidden" />
                {!cameraReady && !running && !previewOnly && (
                  <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-slate-900/75 p-3 text-center text-xs text-slate-200">
                    {loading ? "Carregando…" : "Abra o menu e selecione a câmera ou adicione um vídeo"}
                  </div>
                )}
                {awaitingVideoStart && (
                  <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-slate-900/80 px-2 py-1 text-center text-[11px] text-slate-100">
                    {preparingPipeline
                      ? "Preparando linha e detecção… aguarde."
                      : pipelineReady
                        ? "Pronto. Clique em Iniciar contagem."
                        : "Preparação pendente. Aguarde ou recarregue o vídeo."}
                  </div>
                )}
              </div>
            </div>
            <div className="relative flex min-h-0 flex-col overflow-hidden rounded-lg border border-[var(--rovah-border)] bg-white shadow-sm">
              <p className="panel-heading shrink-0 px-2 py-0.5 text-center">
                Processador
              </p>
              <div className="relative min-h-0 flex-1 bg-slate-950">
                <canvas ref={processorCanvasRef} className="h-full w-full object-contain" />
                {!hasProcessorOverlay && !running && !previewOnly && (
                  <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-[var(--rovah-bg)] text-center text-xs text-[var(--rovah-text-muted)]">
                    Preview do processador
                  </div>
                )}
                {videoFileName && videoDuration > 0 && (
                  <VideoDurationOverlay currentTime={videoCurrentTime} duration={videoDuration} />
                )}
              </div>
            </div>
          </div>

          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <div className="pointer-events-auto flex flex-col items-center gap-2 rounded-2xl border border-white/15 bg-slate-950/75 px-3 py-3 shadow-2xl shadow-slate-950/40 backdrop-blur-md">
              <ControlButton
                icon={<Pause className="h-5 w-5" strokeWidth={1.75} />}
                label="Pausar contagem"
                tone="warning"
                disabled={!running || paused || previewOnly || loading || preparingPipeline}
                onClick={handlePause}
              />
              <ControlButton
                icon={<Play className="h-5 w-5" strokeWidth={1.75} />}
                label={awaitingVideoStart ? "Iniciar contagem" : "Retomar contagem"}
                tone="success"
                disabled={!canResumeCounting || loading || preparingPipeline}
                onClick={() => void handleResume()}
              />
              <ControlButton
                icon={<RotateCcw className="h-5 w-5" strokeWidth={1.75} />}
                label="Reiniciar video"
                tone="primary"
                disabled={!canRestartVideo}
                onClick={() => void handleRestartVideo()}
              />
              <ControlButton
                icon={<Square className="h-5 w-5" strokeWidth={1.75} />}
                label="Parar contagem"
                tone="danger"
                disabled={
                  (!running && !previewOnly && !cameraReady) || loading || preparingPipeline
                }
                onClick={() => void handleStop()}
              />
            </div>
          </div>
        </div>
      </section>

      <section className="grid shrink-0 grid-cols-2 gap-1.5 sm:grid-cols-3 lg:grid-cols-6">
        <InfoCard
          title="Total de ovos"
          value={String(totalOvos)}
          accent="danger"
          icon={<Egg className="h-5 w-5" strokeWidth={1.75} />}
        />
        <InfoCard
          title="Acumulado do dia"
          value={String(dailyTotal)}
          accent="success"
          icon={<CalendarCheck className="h-5 w-5" strokeWidth={1.75} />}
        />
        <InfoCard
          title="Status"
          value={isOn ? "LIGADO" : "DESLIGADO"}
          accent={isOn ? "success" : "default"}
          icon={<Power className="h-5 w-5" strokeWidth={1.75} />}
        />
        <InfoCard
          title="Granja"
          icon={<Building2 className="h-5 w-5" strokeWidth={1.75} />}
        >
          <select
            className="info-card-field mt-1 w-full text-[10px]"
            value={selectedGranja}
            disabled={running || loading}
            onChange={(e) => handleGranjaChange(e.target.value)}
          >
            {GRANJA_OPTIONS.map((granja) => (
              <option key={granja} value={granja}>
                {granja}
              </option>
            ))}
          </select>
        </InfoCard>
        <InfoCard title="Lote" icon={<Layers className="h-5 w-5" strokeWidth={1.75} />}>
          <div className="mt-1 flex w-full items-center justify-center gap-1">
            <input
              type="text"
              inputMode="numeric"
              maxLength={4}
              value={loteDigits}
              disabled={running || loading}
              onChange={(e) => handleLoteDigitsChange(e.target.value)}
              onBlur={() => persistLote(loteDigits, loteSiglas)}
              className="info-card-field w-[3.2rem] text-xs tracking-widest"
              aria-label="Quatro dígitos do lote"
              placeholder="0000"
            />
            <span className="text-sm font-bold text-[var(--rovah-text-muted)]">-</span>
            <input
              type="text"
              maxLength={2}
              value={loteSiglas}
              disabled={running || loading}
              onChange={(e) => handleLoteSiglasChange(e.target.value)}
              onBlur={() => persistLote(loteDigits, loteSiglas)}
              className="info-card-field w-[2.2rem] text-xs uppercase tracking-widest"
              aria-label="Siglas do lote"
              placeholder="AA"
            />
          </div>
        </InfoCard>
        <InfoCard title="Relatorio" icon={<FileText className="h-5 w-5" strokeWidth={1.75} />}>
          <button
            type="button"
            disabled={reportLoading || loading}
            onClick={() => void handleGenerateReport()}
            className="mt-1 inline-flex w-full items-center justify-center gap-1 rounded-md border border-[var(--rovah-green)] bg-[rgba(155,203,59,0.12)] px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-[var(--rovah-green-dark)] transition hover:bg-[rgba(155,203,59,0.22)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {reportLoading ? "Gerando…" : "Gerar PDF"}
          </button>
        </InfoCard>
      </section>
    </div>
  );
}
