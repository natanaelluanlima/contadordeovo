# Egg — Gateway

Repositório: https://github.com/gruponeural/java-egg-gateway.git

Ponto de entrada HTTP do ecossistema **Egg**. Valida assinaturas HMAC das requisições vindas do site e encaminha chamadas ao BFF via Apache Camel.

## O que faz

- Recebe requisições do front-end (via proxy Next.js)
- Valida cabeçalhos `X-Signature` e `X-Timestamp` (HMAC-SHA256)
- Roteia rotas de contagem para o BFF
- Expõe health check

## Stack

- Java 21, Quarkus 3, Apache Camel

## Requisitos

- JDK 21
- BFF em execução na porta `9001`

## Como subir

Linux/macOS:

```bash
cd java/gateway
./mvnw quarkus:dev
```

Windows (PowerShell):

```powershell
cd java/gateway
$env:JAVA_HOME = "C:\Program Files\Zulu\zulu-21"
.\mvnw.cmd quarkus:dev
```

| Item | Valor |
|------|-------|
| Porta | **9000** |
| Root path | `/gruponeural/egg/gateway/` |
| Health | http://localhost:9000/gruponeural/egg/gateway/health |

## Rotas de contagem

| Entrada no gateway | Encaminha ao BFF |
|--------------------|------------------|
| `GET /contagem/screen/status` | `GET /v1/screen/contagem/status` |
| `POST /contagem/screen/iniciar` | `POST /v1/screen/contagem/iniciar` |
| `POST /contagem/screen/parar` | `POST /v1/screen/contagem/parar` |
| `POST /contagem/screen/frame-b64` | `POST /v1/screen/contagem/frame-b64` |

## Configuração

Segredo de assinatura em `src/main/resources/application.properties`:

```properties
public.validator.secret=...
```

Deve ser o mesmo valor de `EGG_GATEWAY_SIGNATURE_SECRET` no site (`react/egg/.env.local`).

## Ordem na stack

Suba **depois** do BFF e **antes** do site:

```
Processador → BFF → Gateway → Site
```
