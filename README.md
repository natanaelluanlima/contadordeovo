# Egg — Contagem de ovos

Workspace local do ecossistema **Egg**: contagem automática de ovos em esteira de produção com visão computacional. O fluxo conecta um site Next.js a serviços Java (Gateway e BFF) e a um processador Python.

## Arquitetura

```
Site (Next.js)  →  Gateway (Quarkus/Camel)  →  BFF (Quarkus)  →  Processador (Python)
   :8009                    :9000                    :9001                  :9002
```

## Projetos

| Projeto | Pasta | Porta | Resumo |
|---------|-------|-------|--------|
| **Site** | [`react/egg`](react/egg) | 8009 | Interface web da demo de contagem (câmera ou vídeo) |
| **Gateway** | [`java/gateway`](java/gateway) | 9000 | Entrada HTTP, validação HMAC e roteamento ao BFF |
| **BFF** | [`java/bff`](java/bff) | 9001 | Orquestra as APIs consumidas pelo site e chama o processador |
| **Processador** | [`python/egg`](python/egg) | 9002 | Detecção, tracking e contagem com OpenCV |

Documentação detalhada de cada um:

- [Site (Next.js)](react/egg/README.md)
- [Gateway (Java)](java/gateway/README.md)
- [BFF (Java)](java/bff/README.md)
- [Processador (Python)](python/egg/README.md)

## Requisitos

- **Node.js** LTS — site
- **JDK 21** — gateway e BFF
- **Python 3.10+** — processador

## Subir tudo

### Atalho rapido (Windows)

1. **Duplo clique** em [`iniciar-contador.bat`](iniciar-contador.bat) na raiz do projeto, ou use o atalho **Contador de Ovos** na area de trabalho.
2. O script sobe os 4 servicos em segundo plano (processador, BFF, gateway e site) e abre o navegador em http://localhost:8009/contagem. Os logs ficam na pasta [`logs`](logs).
3. Para encerrar, use [`parar-contador.bat`](parar-contador.bat) ou o atalho **Parar Contador de Ovos**.

Via PowerShell:

```powershell
.\scripts\iniciar-contador.ps1          # sobe tudo
.\scripts\iniciar-contador.ps1 -AbrirNavegador
.\scripts\parar-contador.ps1            # para tudo
.\scripts\atualizar-contador.ps1        # busca atualizacoes do GitHub
```

### Atualizar quando outro colaborador der push

O Git nao atualiza sozinho. Use o script de atualizacao:

1. **Manual:** duplo clique em [`atualizar-contador.bat`](atualizar-contador.bat) ou rode `.\scripts\atualizar-contador.ps1`
2. **Automatico (a cada 10 min):** rode uma vez como administrador:

```powershell
.\scripts\atualizar-contador.ps1 -Agendar
```

Para remover o agendamento:

```powershell
.\scripts\atualizar-contador.ps1 -RemoverAgendamento
```

O script usa `git pull --ff-only` (so avanca se nao houver conflito) e ignora o pull se voce tiver alteracoes locais sem commit. Logs em [`logs/atualizar.log`](logs/atualizar.log).

### Manual (um terminal por servico)

Abra um terminal para cada serviço, nesta ordem:

```powershell
# 1 — Processador
cd python/egg
python -m pip install -e .
python -m egg_counter.processador_main

# 2 — BFF
cd java/bff
$env:JAVA_HOME = "C:\Program Files\Zulu\zulu-21"   # ajuste conforme seu JDK
.\mvnw.cmd quarkus:dev

# 3 — Gateway
cd java/gateway
$env:JAVA_HOME = "C:\Program Files\Zulu\zulu-21"
.\mvnw.cmd quarkus:dev

# 4 — Site
cd react/egg
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

**Demo:** http://localhost:8009/contagem

> Use `http://localhost` (não o IP da rede) para a câmera do navegador funcionar.

## Links úteis (dev)

| Serviço | URL |
|---------|-----|
| Demo | http://localhost:8009/contagem |
| Health Gateway | http://localhost:9000/gruponeural/egg/gateway/health |
| Swagger BFF | http://localhost:9001/gruponeural/egg/bff/documentacao |
| Health Processador | http://localhost:9002/gruponeural/egg/processador/health |

## Vídeos de teste

A pasta [`videos`](videos) contém arquivos para validar a contagem, por exemplo:

- `VIDEO PARA TESTES.mp4` — esteira simples, ovos brancos (848×478)
- `VIDEO PADRÃO.mp4` — esteira dupla, ovos marrons (960×540)

O processador seleciona o perfil de calibração automaticamente conforme a resolução do frame.

## Repositórios Git

A pasta raiz `contador` **não** é um repositório Git. Cada serviço tem seu próprio `.git`:

| Projeto | Repositório |
|---------|-------------|
| Site | [gruponeural/react-egg](https://github.com/gruponeural/react-egg.git) |
| Gateway | [gruponeural/java-egg-gateway](https://github.com/gruponeural/java-egg-gateway.git) |
| BFF | [gruponeural/java-egg-bff](https://github.com/gruponeural/java-egg-bff.git) |
| Processador | [gruponeural/python-egg](https://github.com/gruponeural/python-egg.git) |

Após clonar o BFF, inicialize o submódulo `java-core`:

```powershell
cd java/bff
git submodule update --init --recursive
```
