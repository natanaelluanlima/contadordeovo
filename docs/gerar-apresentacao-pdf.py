# -*- coding: utf-8 -*-
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos

DOCS = Path(r"D:\contador\docs")
OUT = DOCS / "Contador-de-Ovos-Apresentacao.pdf"
DARK=(47,54,64); GREEN=(155,203,59); GREEN_DARK=(127,171,46); MUTED=(100,116,139); TEXT=(47,54,64); WHITE=(255,255,255)

class P(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.add_font("Body", "", r"C:\Windows\Fonts\arial.ttf")
        self.add_font("Body", "B", r"C:\Windows\Fonts\arialbd.ttf")
        self.add_font("Body", "I", r"C:\Windows\Fonts\ariali.ttf")
    def header(self):
        if self.page_no() == 1: return
        self.set_fill_color(*DARK); self.rect(0,0,210,14,"F"); self.set_fill_color(*GREEN); self.rect(0,14,210,1.6,"F")
        self.set_text_color(*WHITE); self.set_font("Body","B",9); self.set_xy(12,4)
        self.cell(0,6,"Egg Vision AI  |  Contador de Ovos", align="L")
        self.set_font("Body","",8); self.set_xy(12,4); self.cell(186,6,f"Página {self.page_no()}", align="R"); self.ln(16)
    def footer(self):
        self.set_y(-12); self.set_draw_color(*GREEN); self.set_line_width(0.4); self.line(12,self.get_y(),198,self.get_y())
        self.set_y(-10); self.set_font("Body","",7.5); self.set_text_color(*MUTED)
        self.cell(0,6,"Documento confidencial de apresentação  |  Uso interno e supervisão", align="C")

def st(pdf,t):
    pdf.set_font("Body","B",13); pdf.set_text_color(*DARK); pdf.cell(0,8,t,new_x=XPos.LMARGIN,new_y=YPos.NEXT)
    pdf.set_draw_color(*GREEN); pdf.set_line_width(0.8); y=pdf.get_y(); pdf.line(12,y,55,y); pdf.ln(4)
def bd(pdf,t,s=10):
    pdf.set_font("Body","",s); pdf.set_text_color(*TEXT); pdf.multi_cell(0,5.2,t); pdf.ln(2)
def bu(pdf,t):
    x=pdf.get_x(); pdf.set_fill_color(*GREEN); pdf.ellipse(x+1,pdf.get_y()+1.6,2.2,2.2,"F"); pdf.set_xy(x+6,pdf.get_y())
    pdf.set_font("Body","",10); pdf.set_text_color(*TEXT); pdf.multi_cell(180,5.2,t); pdf.ln(1.2)

pdf=P(); pdf.set_auto_page_break(True,16); pdf.set_margins(12,16,12)
pdf.add_page(); pdf.set_fill_color(*DARK); pdf.rect(0,0,210,78,"F"); pdf.set_fill_color(*GREEN); pdf.rect(0,78,210,3.5,"F")
if (DOCS/"icone.png").exists(): pdf.image(str(DOCS/"icone.png"),x=16,y=14,w=22)
if (DOCS/"logo.png").exists(): pdf.image(str(DOCS/"logo.png"),x=168,y=12,w=28)
pdf.set_xy(44,18); pdf.set_font("Body","",11); pdf.set_text_color(*GREEN); pdf.cell(0,6,"EGG VISION AI")
pdf.set_xy(44,28); pdf.set_font("Body","B",26); pdf.set_text_color(*WHITE); pdf.cell(0,10,"CONTADOR DE OVOS")
pdf.set_xy(44,42); pdf.set_font("Body","",12); pdf.set_text_color(220,230,240)
pdf.multi_cell(120,5.5,"Solução de contagem ao vivo para linhas de produção\nem granjas e unidades de beneficiamento.")
pdf.set_xy(16,62); pdf.set_font("Body","",9); pdf.set_text_color(180,190,200)
pdf.cell(0,5,"Apresentação técnica e operacional  |  Foco: contagem em tempo real com câmera")
pdf.set_y(92); st(pdf,"O que é o programa")
bd(pdf,"O Contador de Ovos é um sistema inteligente que acompanha a esteira de produção em tempo real. Uma câmera enxerga os ovos passando, o software identifica cada um e registra a passagem pela linha de contagem — sem necessidade de marcar, parar ou contar manualmente.")
bd(pdf,"O projeto foi pensado para o produtor e para a supervisão: tela clara, total visível, operação simples e resultado confiável no ritmo da linha.")
if (DOCS/"doc-contagem-ao-vivo.png").exists():
    pdf.image(str(DOCS/"doc-contagem-ao-vivo.png"),x=12,y=pdf.get_y()+2,w=186,h=72); pdf.set_y(pdf.get_y()+76)
    pdf.set_font("Body","I",8); pdf.set_text_color(*MUTED)
    pdf.cell(0,4,"Figura 1 — Contagem ao vivo: câmera + esteira + ovos em movimento", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.ln(2); st(pdf,"Para quem foi feito")
bu(pdf,"Produtor: acompanhar o volume da linha com praticidade.")
bu(pdf,"Supervisor: validar produtividade e padronizar o processo.")
bu(pdf,"Equipe de planta: operar com poucos cliques e feedback visual imediato.")

pdf.add_page(); st(pdf,"Como funciona a contagem ao vivo")
bd(pdf,"O modo principal do sistema é a contagem em tempo real com câmera integrada na linha. O vídeo gravado existe apenas como ferramenta de teste e calibração; o trabalho diário é contar o ovo que está passando agora.")
if (DOCS/"doc-fluxo-sistema.png").exists():
    pdf.image(str(DOCS/"doc-fluxo-sistema.png"),x=12,y=pdf.get_y(),w=186,h=58); pdf.set_y(pdf.get_y()+62)
    pdf.set_font("Body","I",8); pdf.set_text_color(*MUTED)
    pdf.cell(0,4,"Figura 2 — Fluxo simplificado: captura, detecção, rastreio e total", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT); pdf.ln(2)
st(pdf,"Passo a passo operacional")
for title,text in [
("1. Captura ao vivo","A câmera filma a esteira continuamente. O sistema recebe o quadro atual da linha — o mesmo que o operador vê na tela."),
("2. Detecção inteligente","Um modelo de visão computacional localiza cada ovo na imagem, mesmo com esteira perfurada, variação de luz e ovos próximos entre si."),
("3. Acompanhamento na linha","Cada ovo recebe um acompanhamento visual enquanto se move. Assim o sistema não conta o mesmo ovo duas vezes."),
("4. Contagem na linha virtual","Quando o ovo cruza a linha de contagem definida na tela, o total é atualizado imediatamente — em tempo real."),
("5. Registro e supervisão","O operador informa granja e lote, acompanha o acumulado do dia e pode gerar relatório ao encerrar o turno."),
]:
    pdf.set_font("Body","B",10); pdf.set_text_color(*GREEN_DARK); pdf.cell(0,5.5,title,new_x=XPos.LMARGIN,new_y=YPos.NEXT)
    pdf.set_font("Body","",9.5); pdf.set_text_color(*TEXT); pdf.multi_cell(0,4.8,text); pdf.ln(1.2)
st(pdf,"Por que priorizar o ao vivo")
bu(pdf,"Reflete a produção real do momento, não uma gravação antiga.")
bu(pdf,"Permite reagir na hora a falhas de fluxo, paradas ou acúmulo na esteira.")
bu(pdf,"Reduz dependência de contagem manual e inconsistências entre turnos.")
bu(pdf,"Prepara a operação para uso contínuo com câmera instalada na planta.")

pdf.add_page(); st(pdf,"O que o operador vê na prática")
bd(pdf,"Ao iniciar o Contador, o sistema sobe automaticamente e abre a tela de trabalho. Com a câmera ligada, o preview mostra a esteira ao vivo, os ovos destacados e o total crescendo a cada passagem pela linha de contagem.")
bd(pdf,"Controles principais: iniciar/pausar contagem, informar granja e lote, acompanhar acumulado do dia e desligar o sistema com segurança ao final.")
y=pdf.get_y()+2; pdf.set_fill_color(236,245,214); pdf.set_draw_color(*GREEN); pdf.set_line_width(0.5); pdf.rect(12,y,186,28,"DF")
pdf.set_xy(16,y+4); pdf.set_font("Body","B",10); pdf.set_text_color(*DARK); pdf.cell(0,5,"Ponto central do projeto")
pdf.set_xy(16,y+11); pdf.set_font("Body","",9.5); pdf.set_text_color(*TEXT)
pdf.multi_cell(178,4.8,"Contar ovos ao vivo, com câmera na esteira, de forma automática, rastreável e compreensível para quem opera a granja — do chão de produção à supervisão.")
pdf.set_y(y+32)
st(pdf,"Benefícios para a supervisão")
bu(pdf,"Padronização: todos os turnos usam o mesmo critério de contagem.")
bu(pdf,"Transparência: total e status visíveis na tela durante a operação.")
bu(pdf,"Agilidade: menos tempo gasto em contagem manual e conferência.")
bu(pdf,"Escalabilidade: base pronta para câmera permanente na linha.")
st(pdf,"Requisitos de uso em campo")
bu(pdf,"Câmera posicionada de forma estável sobre a esteira (boa iluminação).")
bu(pdf,"Computador local com o Contador instalado (início por atalho único).")
bu(pdf,"Definição da linha de contagem e área de interesse na imagem.")
bu(pdf,"Operador treinado no fluxo: ligar, contar, pausar e desligar.")
st(pdf,"Observação sobre vídeo gravado")
bd(pdf,"Arquivos de vídeo podem ser usados em treinamento, demonstração e ajuste fino do sistema. Eles não substituem a operação real. O objetivo do Contador de Ovos é a contagem contínua ao vivo, integrada à rotina da produção.")
st(pdf,"Encerramento")
bd(pdf,"O Contador de Ovos une visão computacional e usabilidade industrial para entregar um número confiável no momento em que o ovo passa na esteira. É uma ferramenta prática para o produtor e uma base sólida de controle para a supervisão.")
pdf.ln(4); box_y=pdf.get_y(); pdf.set_fill_color(*DARK); pdf.rect(12,box_y,186,22,"F")
pdf.set_xy(16,box_y+5); pdf.set_font("Body","B",11); pdf.set_text_color(*GREEN); pdf.cell(0,5,"Egg Vision AI  —  Contador de Ovos")
pdf.set_xy(16,box_y+12); pdf.set_font("Body","",9); pdf.set_text_color(220,230,240); pdf.cell(0,5,"Contagem ao vivo  |  Simplicidade operacional  |  Foco na produção")
pdf.output(str(OUT)); print(OUT)
