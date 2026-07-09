"use client";

import Image from "next/image";
import {
  Building2,
  CalendarCheck,
  Camera,
  ChevronDown,
  Clock,
  Egg,
  FileVideo,
  Layers,
  Menu,
  Pause,
  Play,
  PlayCircle,
  Power,
  RefreshCw,
  ScanEye,
  Square,
  Video,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import {
  enviarFrame,
  fetchContagemStatus,
  iniciarContagem,
  pararContagem,
  type ContagemStatus,
} from "@/lib/gateway/contagem-api";

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
      ? "text-emerald-600"
      : accent === "danger"
        ? "text-rose-600"
        : "text-slate-800";

  return (
    <article className="info-card-3d flex min-h-[168px] flex-col items-center rounded-xl px-4 py-5 text-center transition-shadow">
      <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full border border-sky-200 bg-sky-50 text-sky-600 shadow-sm">
        {icon}
      </div>
      <div className="text-sm font-semibold tracking-wide text-slate-600">{title}</div>
      {children ?? (
        <div className={`mt-3 text-3xl font-bold md:text-4xl ${valueColor}`}>{value}</div>
      )}
      <div className="mt-4 h-1.5 w-full max-w-[220px] overflow-hidden rounded-full border border-slate-300 bg-slate-200 shadow-inner">
        <div className="h-full w-[78%] rounded-full bg-gradient-to-r from-sky-500 to-cyan-400 shadow-sm" />
      </div>
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
    <div className="pointer-events-none absolute inset-x-3 bottom-3 rounded-lg border border-white/20 bg-slate-950/85 px-3 py-2 shadow-lg backdrop-blur-sm">
      <div className="mb-1.5 flex items-center justify-between gap-3 font-mono text-xs text-slate-200 sm:text-sm">
        <span>Duração do vídeo</span>
        <span className="font-semibold text-white">
          {formatVideoTime(currentTime)} / {formatVideoTime(duration)}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-slate-700">
        <div
          className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-sky-500 transition-[width] duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

function DateTimeCard({ dateTime }: { dateTime: Date }) {
  const date = dateTime.toLocaleDateString("pt-BR", {
    weekday: "long",
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
    <article className="inline-flex flex-wrap items-center justify-center gap-x-3 gap-y-1 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 shadow-sm">
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-sky-50 text-sky-600">
        <Clock className="h-4 w-4" strokeWidth={1.75} />
      </span>
      <span className="font-medium capitalize">{date}</span>
      <span className="font-mono text-base font-semibold text-slate-900">{time}</span>
    </article>
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
          : "border-slate-400/50 bg-slate-500/20 text-slate-100 hover:bg-slate-500/35";

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      aria-label={label}
      title={label}
      className={`flex h-14 w-14 items-center justify-center rounded-full border-2 shadow-lg backdrop-blur-md transition hover:scale-105 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:scale-100 sm:h-16 sm:w-16 ${toneClass}`}
    >
      {icon}
    </button>
  );
}

function MenuItem({ icon, label, onClick, disabled, tone = "default" }: MenuItemProps) {
  const toneClass =
    tone === "primary"
      ? "text-sky-700 hover:bg-sky-50"
      : tone === "success"
        ? "text-emerald-700 hover:bg-emerald-50"
        : tone === "danger"
          ? "text-rose-700 hover:bg-rose-50"
          : "text-slate-700 hover:bg-slate-50";

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-45 ${toneClass}`}
    >
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-slate-200 bg-white text-sky-600">
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
  const captureCanvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileUrlRef = useRef<string | null>(null);
  const loopRef = useRef<number | null>(null);
  const previewLoopRef = useRef<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const activeDeviceIdRef = useRef<string | null>(null);

  const [status, setStatus] = useState<ContagemStatus | null>(null);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
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
  const [selectedGranja, setSelectedGranja] = useState(GRANJA_OPTIONS[0]);
  const [loteDigits, setLoteDigits] = useState("0000");
  const [loteSiglas, setLoteSiglas] = useState("AA");
  const menuRef = useRef<HTMLDivElement>(null);

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
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          {
            deviceId: { exact: deviceId },
            width: { ideal: 640 },
            height: { ideal: 480 },
          },
          { deviceId: { ideal: deviceId } },
        ]
      : [{ width: { ideal: 1280 }, height: { ideal: 720 } }];

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
    setPreview(null);
    setSourceWarning(null);

    for (const canvas of [previewCanvasRef.current, captureCanvasRef.current]) {
      if (!canvas) continue;
      const ctx = canvas.getContext("2d");
      if (!ctx) continue;
      ctx.clearRect(0, 0, canvas.width || 1, canvas.height || 1);
    }
  }, []);

  const stopCountingLoop = useCallback(() => {
    if (loopRef.current) {
      window.clearInterval(loopRef.current);
      loopRef.current = null;
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
    clearPreviewSurfaces();
  }, [clearPreviewSurfaces, stopFrameLoops]);

  const drawLocalPreview = useCallback(() => {
    const video = videoRef.current;
    const canvas = previewCanvasRef.current;
    if (!video || !canvas || video.readyState < 2) return false;

    const width = video.videoWidth;
    const height = video.videoHeight;
    if (!width || !height) return false;

    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) return false;
    ctx.drawImage(video, 0, 0, width, height);
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
    loopRef.current = window.setInterval(async () => {
      const video = videoRef.current;
      const canvas = captureCanvasRef.current;
      if (!video || !canvas || video.readyState < 2 || video.ended) {
        if (video?.ended) {
          void handleVideoEnded();
        }
        return;
      }

      const width = video.videoWidth;
      const height = video.videoHeight;
      if (!width || !height) return;

      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(video, 0, 0, width, height);

      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob((b) => resolve(b), "image/jpeg", 0.75)
      );
      if (!blob) return;

      try {
        const data = await enviarFrame(blob);
        setStatus(data);
        if (data.annotated_frame_b64) {
          setPreview(`data:image/jpeg;base64,${data.annotated_frame_b64}`);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Falha ao enviar frame");
      }
    }, 200);
  }, [handleVideoEnded]);

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
      setPreviewOnly(false);
      setPaused(false);
      setRunning(true);
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
    stopPlayback,
  ]);

  const startVideoFile = useCallback(
    async (file: File) => {
      setError(null);
      setLoading(true);
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

        video.currentTime = 0;
        video.pause();
        setCameraReady(true);
        drawLocalPreview();
        setPreviewOnly(true);
        setRunning(false);
        setPaused(false);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Falha ao carregar o vídeo");
        stopPlayback();
      } finally {
        setLoading(false);
      }
    },
    [drawLocalPreview, handleVideoEnded, stopPlayback]
  );

  const handleStop = useCallback(async () => {
    const wasCounting = running;
    stopPlayback();
    setPaused(false);
    if (!wasCounting) return;

    try {
      const data = await pararContagem();
      setStatus(data);
      accumulateSessionCount(data.total_count);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao parar");
    }
  }, [accumulateSessionCount, running, stopPlayback]);

  const handlePause = useCallback(() => {
    stopCountingLoop();
    videoRef.current?.pause();
    setPaused(true);
  }, [stopCountingLoop]);

  const handleResume = useCallback(async () => {
    const video = videoRef.current;
    if (!video) return;

    setError(null);
    setLoading(true);

    try {
      if (!running && previewOnly && videoFileName) {
        await iniciarContagem("uploaded_video");
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
  }, [paused, previewOnly, running, startFrameLoop, startPreviewLoop, videoFileName]);

  const selectedCameraLabel =
    cameras.find((camera) => camera.deviceId === selectedCameraId)?.label ?? "—";
  const hasSelectionMismatch =
    Boolean(activeDeviceId && selectedCameraId && activeDeviceId !== selectedCameraId);
  const isOn = running && !paused;
  const totalOvos = status?.total_count ?? 0;
  const activeSessionCount = running || paused ? totalOvos : 0;
  const dailyTotal = completedDailyTotal + activeSessionCount;
  const awaitingVideoStart = Boolean(previewOnly && videoFileName && cameraReady && !running);
  const canResumeCounting = (running && paused) || awaitingVideoStart;

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
    <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-6 px-4 py-6 md:px-8">
      <header className="relative overflow-hidden border-b border-slate-200/80 pb-6 pt-4">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.12),transparent_55%)]"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-400/70 to-transparent contador-title-glow"
        />

        <div className="relative flex flex-col items-center gap-3 px-20">
          <div className="flex items-center gap-3">
            <span className="h-px w-10 bg-gradient-to-r from-transparent to-cyan-500/80" />
            <ScanEye className="h-6 w-6 text-cyan-500" strokeWidth={1.75} />
            <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.42em] text-cyan-600/90 sm:text-xs">
              Egg Vision AI
            </span>
            <ScanEye className="h-6 w-6 text-cyan-500" strokeWidth={1.75} />
            <span className="h-px w-10 bg-gradient-to-l from-transparent to-cyan-500/80" />
          </div>

          <h1 className="contador-title text-center text-3xl font-black tracking-[0.1em] md:text-4xl lg:text-5xl">
            CONTADOR DE OVOS
          </h1>

          <p className="max-w-md text-center font-mono text-[11px] uppercase tracking-[0.28em] text-slate-500 sm:text-xs">
            Visão computacional · contagem em tempo real
          </p>
        </div>

        <div className="absolute right-0 top-1/2 -translate-y-1/2">
          <Image
            src="/logo-bica-meu-galo.png"
            alt="Bica Meu Galo"
            width={96}
            height={96}
            className="rounded-full border border-slate-200 bg-white shadow-sm"
            priority
          />
        </div>
      </header>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-center text-sm text-rose-700">
          {error}
        </div>
      )}

      <section className="flex flex-col items-center gap-4">
        <div ref={menuRef} className="relative w-full max-w-xl">
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
          >
            <Menu className="h-5 w-5 text-sky-600" strokeWidth={1.75} />
            Menu de contagem
            <ChevronDown
              className={`h-4 w-4 text-slate-500 transition ${menuOpen ? "rotate-180" : ""}`}
              strokeWidth={1.75}
            />
          </button>

          {menuOpen && (
            <div className="absolute left-0 right-0 z-20 mt-2 rounded-xl border border-slate-200 bg-white p-3 shadow-xl">
              <label className="mb-2 flex flex-col gap-2 rounded-lg border border-slate-100 bg-slate-50 p-3">
                <span className="flex items-center justify-center gap-2 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <Camera className="h-4 w-4 text-sky-600" strokeWidth={1.75} />
                  Selecionar câmera
                </span>
                <select
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-center text-sm text-slate-700 disabled:opacity-50"
                  value={selectedCameraId}
                  disabled={running || loading || loadingCameras || cameras.length === 0}
                  onChange={(e) => handleCameraSelection(e.target.value)}
                >
                  {cameras.length === 0 ? (
                    <option value="">Nenhuma câmera detectada</option>
                  ) : (
                    cameras.map((camera) => (
                      <option key={camera.deviceId} value={camera.deviceId}>
                        {camera.label}
                      </option>
                    ))
                  )}
                </select>
              </label>

              <div className="space-y-1">
                <MenuItem
                  icon={<RefreshCw className="h-4 w-4" strokeWidth={1.75} />}
                  label={loadingCameras ? "Listando câmeras…" : "Atualizar câmeras"}
                  disabled={running || loading || loadingCameras}
                  onClick={() => void loadCameras(true)}
                />
                <MenuItem
                  icon={<Video className="h-4 w-4" strokeWidth={1.75} />}
                  label={loading && previewOnly ? "Testando câmera…" : "Testar câmera"}
                  disabled={running || loading || cameras.length === 0}
                  onClick={() => void testCamera()}
                />
                <MenuItem
                  icon={<PlayCircle className="h-4 w-4" strokeWidth={1.75} />}
                  label={loading ? "Iniciando câmera…" : "Iniciar câmera"}
                  tone="success"
                  disabled={running || loading || cameras.length === 0}
                  onClick={() => void startCamera()}
                />
                <MenuItem
                  icon={<FileVideo className="h-4 w-4" strokeWidth={1.75} />}
                  label={loading ? "Carregando vídeo…" : "Adicionar vídeo"}
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
      </section>

      {(cameras.length > 0 && cameras.every((camera) => camera.label.startsWith("Câmera "))) ||
      streamInfo ||
      hasSelectionMismatch ||
      videoFileName ? (
        <section className="rounded-xl border border-slate-200 bg-white p-4 text-center text-sm text-slate-600 shadow-sm">
          {cameras.length > 0 && cameras.every((camera) => camera.label.startsWith("Câmera ")) && (
            <p>
              Os nomes podem aparecer genéricos até você clicar em &quot;Atualizar câmeras&quot; e
              permitir o acesso.
            </p>
          )}
          {streamInfo && <p>Fonte ativa: {streamInfo}</p>}
          {hasSelectionMismatch && (
            <p className="text-amber-700">
              Selecionada: {selectedCameraLabel}. Clique em &quot;Testar câmera&quot; para trocar a
              fonte ativa.
            </p>
          )}
          {videoFileName && (
            <p>
              Vídeo em uso: <span className="font-medium text-slate-800">{videoFileName}</span>
            </p>
          )}
        </section>
      ) : null}

      {sourceWarning && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-center text-sm text-amber-800">
          {sourceWarning}
        </div>
      )}

      <section className="flex flex-col gap-3">
        <div className="relative">
          <div className="grid flex-1 gap-4 md:grid-cols-2">
            <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <p className="border-b border-slate-100 px-3 py-2 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">
                Ao vivo
              </p>
              <video ref={videoRef} className="hidden" autoPlay muted playsInline />
              <canvas
                ref={previewCanvasRef}
                className="aspect-video w-full bg-slate-950 object-contain"
              />
              <canvas ref={captureCanvasRef} className="hidden" />
              {!cameraReady && !running && !previewOnly && (
                <div className="pointer-events-none absolute inset-0 top-9 flex items-center justify-center bg-slate-900/75 p-4 text-center text-sm text-slate-200">
                  {loading ? "Carregando…" : "Abra o menu e selecione a câmera ou adicione um vídeo"}
                </div>
              )}
              {awaitingVideoStart && (
                <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-slate-900/80 px-4 py-2 text-center text-sm text-slate-100">
                  Vídeo carregado. Use o botão play para iniciar.
                </div>
              )}
            </div>
            <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <p className="border-b border-slate-100 px-3 py-2 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">
                Processador
              </p>
              {preview ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={preview} alt="Frame processado" className="aspect-video w-full bg-slate-950 object-contain" />
              ) : (
                <div className="flex aspect-video items-center justify-center bg-slate-100 text-center text-sm text-slate-500">
                  Preview do processador
                </div>
              )}
              {videoFileName && videoDuration > 0 && (
                <VideoDurationOverlay currentTime={videoCurrentTime} duration={videoDuration} />
              )}
            </div>
          </div>

          <div className="pointer-events-none absolute inset-0 top-9 flex items-center justify-center">
            <div className="pointer-events-auto flex flex-col items-center gap-3 rounded-3xl border border-white/15 bg-slate-950/75 px-4 py-4 shadow-2xl shadow-slate-950/40 backdrop-blur-md sm:gap-4 sm:px-5 sm:py-5">
              <ControlButton
                icon={<Pause className="h-6 w-6 sm:h-7 sm:w-7" strokeWidth={1.75} />}
                label="Pausar contagem"
                tone="warning"
                disabled={!running || paused || previewOnly || loading}
                onClick={handlePause}
              />
              <ControlButton
                icon={<Play className="h-6 w-6 sm:h-7 sm:w-7" strokeWidth={1.75} />}
                label={awaitingVideoStart ? "Iniciar contagem" : "Retomar contagem"}
                tone="success"
                disabled={!canResumeCounting || loading}
                onClick={() => void handleResume()}
              />
              <ControlButton
                icon={<Square className="h-6 w-6 sm:h-7 sm:w-7" strokeWidth={1.75} />}
                label="Parar contagem"
                tone="danger"
                disabled={(!running && !previewOnly && !cameraReady) || loading}
                onClick={() => void handleStop()}
              />
            </div>
          </div>
        </div>

        <div className="flex justify-center">
          <DateTimeCard dateTime={now} />
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <InfoCard
          title="TOTAL DE OVOS"
          value={String(totalOvos)}
          accent="danger"
          icon={<Egg className="h-5 w-5" strokeWidth={1.75} />}
        />
        <InfoCard
          title="CONTAGEM ACUMULADA DO DIA"
          value={String(dailyTotal)}
          accent="success"
          icon={<CalendarCheck className="h-5 w-5" strokeWidth={1.75} />}
        />
        <InfoCard
          title="STATUS"
          value={isOn ? "LIGADO" : "DESLIGADO"}
          accent={isOn ? "success" : "default"}
          icon={<Power className="h-5 w-5" strokeWidth={1.75} />}
        />
        <InfoCard
          title="NOME DA GRANJA"
          icon={<Building2 className="h-5 w-5" strokeWidth={1.75} />}
        >
          <select
            className="info-card-field mt-3 text-xs sm:text-sm"
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
      </section>

      <section className="flex justify-center">
        <div className="w-full max-w-sm">
          <InfoCard title="LOTE" icon={<Layers className="h-5 w-5" strokeWidth={1.75} />}>
            <div className="mt-3 flex w-full max-w-[220px] items-center justify-center gap-2">
              <input
                type="text"
                inputMode="numeric"
                maxLength={4}
                value={loteDigits}
                disabled={running || loading}
                onChange={(e) => handleLoteDigitsChange(e.target.value)}
                onBlur={() => persistLote(loteDigits, loteSiglas)}
                className="info-card-field w-[5.5rem] font-mono text-lg tracking-widest"
                aria-label="Quatro dígitos do lote"
                placeholder="0000"
              />
              <span className="text-xl font-bold text-slate-400">-</span>
              <input
                type="text"
                maxLength={2}
                value={loteSiglas}
                disabled={running || loading}
                onChange={(e) => handleLoteSiglasChange(e.target.value)}
                onBlur={() => persistLote(loteDigits, loteSiglas)}
                className="info-card-field w-[3.5rem] font-mono text-lg uppercase tracking-widest"
                aria-label="Siglas do lote"
                placeholder="AA"
              />
            </div>
            <p className="mt-2 font-mono text-xs font-semibold text-slate-500">
              {loteDigits.padStart(4, "0")}-{loteSiglas.padEnd(2, "A").slice(0, 2).toUpperCase()}
            </p>
          </InfoCard>
        </div>
      </section>
    </div>
  );
}
