# Egg — BFF

Repositório: https://github.com/gruponeural/java-egg-bff.git

**Backend for Frontend** do projeto **Egg**. API consumida pelo site (via Gateway) que orquestra o processador Python de visão computacional.

## O que faz

- Expõe endpoints `/v1/screen/contagem/*` para a demo de contagem
- Repassa frames e comandos de sessão ao processador Python
- Agrega outros módulos da plataforma Cortex (usuários, sessão, localização, etc.)

## Stack

- Java 21, Quarkus 3, REST Client, OpenAPI/Swagger

## Requisitos

- JDK 21
- Processador Python em execução na porta `9002`
- Submódulo [`java-core`](https://github.com/gruponeural/java-core.git) (branch `develop`)

Após clonar:

```powershell
cd java/bff
git submodule update --init --recursive
```

## Como subir

Linux/macOS:

```bash
cd java/bff
./mvnw quarkus:dev
```

Windows (PowerShell):

```powershell
cd java/bff
$env:JAVA_HOME = "C:\Program Files\Zulu\zulu-21"
.\mvnw.cmd quarkus:dev
```

| Item | Valor |
|------|-------|
| Porta | **9001** |
| Root path | `/gruponeural/egg/bff/` |
| Swagger | http://localhost:9001/gruponeural/egg/bff/documentacao |

## API de contagem

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/v1/screen/contagem/status` | Status da sessão |
| `POST` | `/v1/screen/contagem/iniciar` | Inicia contagem (`mode`: `browser_camera`, `uploaded_video`) |
| `POST` | `/v1/screen/contagem/parar` | Encerra sessão |
| `POST` | `/v1/screen/contagem/frame-b64` | Envia frame em base64 |

## Downstream

O BFF chama o processador em:

```
http://localhost:9002/gruponeural/egg/processador
```

Configurado em `application.properties`:

```properties
quarkus.rest-client."egg-processador".url=http://localhost:9002
```

## Ordem na stack

Suba **depois** do processador e **antes** do gateway:

```
Processador → BFF → Gateway → Site
```
