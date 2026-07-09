# Egg — Site (Next.js)

Repositório: https://github.com/gruponeural/react-egg.git

Front-end web do projeto **Egg**. Oferece a demonstração de contagem de ovos em tempo real via câmera do navegador ou upload de vídeo.

## O que faz

- Tela de contagem em `/contagem`
- Seleção de câmera do dispositivo ou envio de vídeo
- Envio periódico de frames ao backend
- Preview ao vivo e frame processado (com ROI, linha de contagem e detecções)

O navegador **não** chama o Gateway diretamente. As requisições passam por `/api/gateway/*` (Route Handler do Next.js), que assina com HMAC e encaminha ao Gateway.

## Stack

- Next.js 16, React 19, TypeScript, Tailwind CSS

## Requisitos

- Node.js LTS
- Gateway (`:9000`), BFF (`:9001`) e Processador (`:9002`) em execução

## Configuração

```powershell
cd react/egg
Copy-Item .env.local.example .env.local
npm install
```

Variáveis em `.env.local`:

| Variável | Descrição |
|----------|-----------|
| `EGG_GATEWAY_BASE_URL` | URL do gateway (ex.: `http://localhost:9000/gruponeural/egg/gateway`) |
| `EGG_GATEWAY_SIGNATURE_SECRET` | Segredo HMAC (igual ao `public.validator.secret` do gateway) |

## Como subir

```powershell
npm run dev
```

| Item | URL |
|------|-----|
| App | http://localhost:8009 |
| Demo | http://localhost:8009/contagem |

Outros scripts:

```powershell
npm run build
npm run start
npm run lint
```

## Fluxo de integração

```
Browser → /api/gateway/* (Next.js) → Gateway :9000 → BFF :9001 → Processador :9002
```

Endpoints usados pela demo (via proxy):

- `GET contagem/screen/status`
- `POST contagem/screen/iniciar`
- `POST contagem/screen/parar`
- `POST contagem/screen/frame-b64`

## Câmera no navegador

- Acesse por **http://localhost:8009** (contexto seguro para `getUserMedia`)
- Use **Testar câmera** antes de iniciar a contagem
- Reinicie a contagem ao trocar de vídeo ou após reiniciar o processador
