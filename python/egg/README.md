# Egg — Processador (Python)

Repositório: https://github.com/gruponeural/python-egg.git

Motor de **visão computacional** do projeto **Egg**. Detecta ovos na esteira, rastreia com centroide e conta cruzamentos em uma linha virtual.

## O que faz

- Recebe frames via API de sessão (consumida pelo BFF)
- Detecta ovos (backend clássico com OpenCV ou YOLOv8)
- Evita contagem duplicada com tracker por centroide
- Retorna contagem, FPS e frame anotado em base64
- Seleciona perfil de calibração automaticamente (848×478 ou 960×540)

Também roda em **modo standalone** com câmera ou arquivo de vídeo, sem a stack Java.

## Stack

- Python 3.10+, OpenCV, Ultralytics YOLOv8 (opcional), FastAPI, Uvicorn

## Estrutura

```
config/
  camera.yaml              # padrão browser / VIDEO PARA TESTES
  runtime.yaml
  camera.video-testes.yaml # calibração VIDEO PARA TESTES.mp4
  camera.video-padrao.yaml # calibração VIDEO PADRÃO.mp4
  reference-*.jpg          # imagens de referência da esteira
src/egg_counter/           # código principal
  dataset.py               # extração de frames para dataset YOLO
```

## Instalação

```powershell
cd python/egg
python -m pip install -e .
```

## Como subir (integração com BFF)

```powershell
cd python/egg
python -m egg_counter.processador_main
```

Com configs explícitas:

```powershell
python -m egg_counter.processador_main `
  --camera-config config/camera.video-padrao.yaml `
  --runtime-config config/runtime.video-padrao.yaml
```

| Item | Valor |
|------|-------|
| Porta | **9002** |
| Root path | `/gruponeural/egg/processador` |
| Health | http://localhost:9002/gruponeural/egg/processador/health |

### Endpoints da sessão

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Health check |
| `GET` | `/v1/session/status` | Status da sessão |
| `POST` | `/v1/session/start` | Inicia sessão |
| `POST` | `/v1/session/stop` | Encerra sessão |
| `POST` | `/v1/session/frame-b64` | Processa frame em base64 |
| `POST` | `/v1/session/frame` | Processa frame multipart |

## Perfis de vídeo

| Vídeo | Resolução | Configs |
|-------|-----------|---------|
| VIDEO PARA TESTES | 848×478 | `camera.yaml` / `camera.video-testes.yaml` |
| VIDEO PADRÃO | 960×540 | `camera.video-padrao.yaml` |

Na demo web, o perfil é escolhido automaticamente pelo tamanho do frame.

## Modo standalone

Processamento local com câmera ou arquivo:

```powershell
python -m egg_counter.main --camera-config config/camera.video-testes.yaml --runtime-config config/runtime.video-testes.yaml
```

## Modelo YOLO

O processador integra **Ultralytics YOLOv8** e, apos o treino local, usa:

```yaml
backend: ultralytics
model_path: models/egg_yolov8n.pt
target_label: egg
```

### Dataset — extração de frames (1 por segundo)

```powershell
python -m egg_counter.dataset --videos-dir videos --output dataset --interval 1
```

### Treino com as fotos

Gera labels automaticamente (detector classico), monta `dataset/yolo-eggs` e treina:

```powershell
python -m egg_counter.train --extract-videos --epochs 40 --device cpu
```

Saida: `models/egg_yolov8n.pt`

## Ordem na stack

Este serviço deve ser o **primeiro** a subir:

```
Processador (:9002) → BFF (:9001) → Gateway (:9000) → Site (:8009)
```
