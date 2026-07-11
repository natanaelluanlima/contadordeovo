import { jsPDF } from "jspdf";

export type ContagemReportInput = {
  granja: string;
  lote: string;
  totalOvos: number;
  startedAt: Date;
  endedAt: Date;
  videoName?: string | null;
};

function formatDatePt(date: Date): string {
  return date.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function formatTimePt(date: Date): string {
  return date.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function drawHeader(doc: jsPDF, pageWidth: number) {
  doc.setFillColor(47, 54, 64);
  doc.rect(0, 0, pageWidth, 42, "F");
  doc.setFillColor(155, 203, 59);
  doc.rect(0, 42, pageWidth, 3, "F");

  doc.setTextColor(245, 248, 250);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text("BICA MEU GALO", 18, 18);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(181, 219, 92);
  doc.text("Solucoes em Contagem Inteligente de Ovos", 18, 27);

  doc.setTextColor(226, 232, 240);
  doc.setFontSize(9);
  doc.text("Relatorio de Contagem", pageWidth - 18, 18, { align: "right" });
  doc.text("Documento oficial do sistema Contador", pageWidth - 18, 27, { align: "right" });
}

function drawFooter(doc: jsPDF, pageWidth: number, pageHeight: number) {
  doc.setDrawColor(155, 203, 59);
  doc.setLineWidth(0.6);
  doc.line(18, pageHeight - 22, pageWidth - 18, pageHeight - 22);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.setTextColor(100, 116, 139);
  doc.text(
    "Bica Meu Galo  |  Contador de Ovos  |  Documento gerado automaticamente",
    pageWidth / 2,
    pageHeight - 14,
    { align: "center" }
  );
  doc.text(`Emitido em ${formatDatePt(new Date())} as ${formatTimePt(new Date())}`, pageWidth / 2, pageHeight - 8, {
    align: "center",
  });
}

export async function generateContagemReportPdf(input: ContagemReportInput): Promise<void> {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  drawHeader(doc, pageWidth);

  let y = 58;
  doc.setTextColor(47, 54, 64);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(14);
  doc.text("Relatorio de Sessao de Contagem", 18, y);

  y += 8;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(100, 116, 139);
  doc.text("Resumo operacional da granja e do lote processado nesta sessao.", 18, y);

  y += 12;
  doc.setFillColor(244, 246, 248);
  doc.roundedRect(18, y, pageWidth - 36, 78, 3, 3, "F");
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(18, y, pageWidth - 36, 78, 3, 3, "S");

  const rows: Array<[string, string]> = [
    ["Granja", input.granja],
    ["Lote", input.lote],
    ["Data", formatDatePt(input.startedAt)],
    ["Horario de inicio", formatTimePt(input.startedAt)],
    ["Horario de fim", formatTimePt(input.endedAt)],
    ["Total de ovos contados", String(input.totalOvos)],
  ];
  if (input.videoName) {
    rows.push(["Fonte de video", input.videoName]);
  }

  let rowY = y + 12;
  for (const [label, value] of rows) {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(100, 116, 139);
    doc.text(label.toUpperCase(), 26, rowY);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(47, 54, 64);
    doc.text(value, 26, rowY + 6);
    rowY += 12;
  }

  y += 92;
  doc.setFillColor(47, 54, 64);
  doc.roundedRect(18, y, pageWidth - 36, 28, 3, 3, "F");
  doc.setFillColor(155, 203, 59);
  doc.rect(18, y, 4, 28, "F");

  doc.setTextColor(248, 250, 252);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.text("Validacao Bica Meu Galo", 28, y + 11);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(203, 213, 225);
  doc.text(
    "Este documento registra a contagem realizada pelo processador inteligente de ovos.",
    28,
    y + 19
  );

  y += 42;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(100, 116, 139);
  doc.text(
    "Assinatura digital do sistema: sessao autenticada pelo Contador Bica Meu Galo.",
    18,
    y
  );

  y += 18;
  doc.setDrawColor(148, 163, 184);
  doc.line(18, y, 88, y);
  doc.line(pageWidth - 88, y, pageWidth - 18, y);
  doc.setFontSize(8);
  doc.text("Responsavel pela granja", 18, y + 5);
  doc.text("Bica Meu Galo", pageWidth - 18, y + 5, { align: "right" });

  drawFooter(doc, pageWidth, pageHeight);

  const safeLote = input.lote.replace(/[^\w-]+/g, "_");
  const stamp = `${input.endedAt.getFullYear()}${String(input.endedAt.getMonth() + 1).padStart(2, "0")}${String(input.endedAt.getDate()).padStart(2, "0")}_${String(input.endedAt.getHours()).padStart(2, "0")}${String(input.endedAt.getMinutes()).padStart(2, "0")}`;
  doc.save(`relatorio-contagem-${safeLote}-${stamp}.pdf`);
}
