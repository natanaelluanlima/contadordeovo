package br.com.gruponeural.core.route;

import java.util.ArrayList;

import org.apache.camel.Exchange;
import org.apache.camel.builder.RouteBuilder;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import br.com.gruponeural.core.helper.RouteHelper;
import br.com.gruponeural.security.JwtValidatorProcessor;
import br.com.gruponeural.security.PublicValidatorProcessor;
import jakarta.inject.Inject;

public abstract class Route
    extends RouteBuilder {

    @ConfigProperty(name = "quarkus.http.root-path", defaultValue = "/")
    String rootPath;

    private String nomeServico;
    private String urlDestino;
    private int httpResponseTimeoutMs = 10_000;
    private ArrayList<RoutePath> listaPath = new ArrayList<>();

    @Inject
    JwtValidatorProcessor jwtValidatorProcessor;

    @Inject
    PublicValidatorProcessor publicValidatorProcessor;

    private void configurarTratamentoExecao() {

        String JSON_MENSAGEM_FALHA_AMIGAVEL = """
                {
                    "id": "${header.X-Correlation-ID}",
                    "mensagemTipo": "falha",
                    "mensagemTitulo": "Falha na comunicação com o servidor.",
                    "mensagemDetalhe": "Por favor, tente novamente mais tarde."
                }
            """;

        String JSON_MENSAGEM_ACESSO_NEGADO = """
                {
                    "id": "${header.X-Correlation-ID}",
                    "mensagemTipo": "falha",
                    "mensagemTitulo": "Acesso não autorizado.",
                    "mensagemDetalhe": "Assinatura do aplicativo inválida ou expirada."
                }
            """;

        onException(SecurityException.class)
            .handled(true)
            .setHeader("Content-Type", constant("application/json"))
            .setHeader("CamelHttpResponseCode", constant(401))
            .setBody(simple(JSON_MENSAGEM_ACESSO_NEGADO))
            .log("⚠️ [SECURITY] Tentativa de acesso negada: ${exception.message}")
            .log("🔙 [RESPOSTA] Status: ${header.CamelHttpResponseCode} de " + this.nomeServico)
            .log("📦 [BODY RESPOSTA]: ${body}")
            .process(exchange -> org.slf4j.MDC.remove("correlationId"));

        onException(Exception.class)

            // 1️⃣ Marca a exceção como tratada para não propagar
            .handled(true)

            // 2️⃣ Log detalhado no console (O MDC coloca ID automaticamente)
            .log("❌ [ERRO NO GATEWAY] Causa: ${exception.message}")
            // Stacktrace apenas no log, nunca no body
            .log("🔍 [STACKTRACE]: ${exception.stacktrace}")

            // 3️⃣ Resposta para o cliente
            .setHeader("Content-Type", constant("application/json"))
            .setHeader("CamelHttpResponseCode", constant(500))

            // Corpo da resposta com detalhes do erro
            .setBody(simple(JSON_MENSAGEM_FALHA_AMIGAVEL))

            // Log do Status
            .log("🔙 [RESPOSTA] Status: ${header.CamelHttpResponseCode} de " + this.nomeServico)

            // Log do Body:
            .log("📦 [BODY RESPOSTA]: ${body}")

            // 4️⃣ Limpeza do MDC para evitar "vazamento" de IDs entre threads
            .process(exchange -> org.slf4j.MDC.remove("correlationId"));

    }

    private void configurarRota(RoutePath path) {

        // O prefixo para o Camel deve ser apenas o nome do serviço,
        // pois o Quarkus já provê o prefixo em quarkus.http.root-path
        String prefixoCamel = this.nomeServico;

        String sufixo = path.getOrigem().startsWith("/") ? path.getOrigem() : "/" + path.getOrigem();
        String endpointFinal = ("/" + prefixoCamel + sufixo).replace("//", "/");

        String consumerUri = "platform-http:" + endpointFinal + "?httpMethodRestrict=" + path.getMetodo();
        if (path.isMatchOnUriPrefix()) {
            consumerUri += "&matchOnUriPrefix=true";
        }

        from(consumerUri)
            .routeId("gateway-" + this.nomeServico + "-" + path.getMetodo() + "-" + sufixo.replaceAll("[/\\?]", "-"))

            .process(exchange -> {
                String corrId = exchange.getIn().getHeader("X-Correlation-ID", String.class);
                boolean corrIdRecebido = corrId != null && !corrId.isBlank();
                if (corrId == null || corrId.isEmpty()) {
                    corrId = java.util.UUID.randomUUID().toString().substring(0, 8);
                }
                exchange.getIn().setHeader("X-Correlation-ID", corrId);
                exchange.getMessage().setHeader("X-Correlation-ID", corrId);
                org.slf4j.MDC.put("correlationId", corrId);
                exchange.setProperty("corrIdRecebido", corrIdRecebido);
            })

            .log("🧭 [CORRELATION] X-Correlation-ID=${header.X-Correlation-ID} | recebido=${exchangeProperty.corrIdRecebido}")
            .log("📥 [ENTRADA] Método: ${header.CamelHttpMethod} | Path: ${header.CamelHttpPath}")

            .choice()
            .when(constant(path.isPreserveBinaryBody()))
            .log("📝 [BODY ENTRADA]: <conteúdo binário/multipart omitido>")
            .otherwise()
            .setBody(simple("${bodyAs(String)}"))
            .process(exchange -> {
                exchange.setProperty("safeBody", RouteHelper.mascararDadosSensiveis(exchange.getIn().getBody(String.class)));
            })
            .log("📝 [BODY ENTRADA]: ${exchangeProperty.safeBody}")
            .end()

            // Ajusta o SubPath para o destino
            .process(exchange -> {
                String pathFinal = path.getDestino();
                if (path.isMatchOnUriPrefix()) {
                    String camelPath = exchange.getIn().getHeader(Exchange.HTTP_PATH, String.class);
                    if (camelPath == null || camelPath.isEmpty()) {
                        camelPath = exchange.getIn().getHeader("CamelHttpPath", String.class);
                    }
                    if (camelPath != null && camelPath.contains("?")) {
                        camelPath = camelPath.substring(0, camelPath.indexOf('?'));
                    }
                    String relMarker = prefixoCamel + "/" + path.getOrigem() + "/";
                    if (camelPath != null) {
                        int idx = camelPath.indexOf(relMarker);
                        if (idx >= 0) {
                            String tail = camelPath.substring(idx + relMarker.length());
                            if (!tail.isEmpty()) {
                                pathFinal = path.getDestino().replaceAll("/$", "") + "/" + tail;
                            }
                        }
                    }
                }
                exchange.getIn().setHeader("SubPath", pathFinal);
            })

            // Assinatura app: obrigatória em todas as rotas (pública ou JWT)
            .log("🔒 [AUTH] Validando X-Signature e X-Timestamp...")
            .process(publicValidatorProcessor)
            .removeHeader("X-Signature")
            .removeHeader("X-Timestamp")

            .choice()
            .when(constant(path.getRequerAutenticacao()))
            .log("🔐 [AUTH] Validando token JWT...")
            .process(jwtValidatorProcessor)
            // Remove o token para o microserviço de destino não tentar validar
            // novamente
            .removeHeader("Authorization")
            // .log("🔐 [AUTH] Token enviado ao destino:
            // ${header.Authorization}")
            .end()

            // Monta a URL de destino (Limpando barra final da base e
            // adicionando o SubPath)
            .setHeader("TargetUrl", simple(urlDestino.replaceAll("/$", "") + "/${header.SubPath}"))

            // Repassa query string (ex.: GET ?foo=) para o HTTP de destino
            .process(exchange -> {
                String q = exchange.getIn().getHeader(Exchange.HTTP_QUERY, String.class);
                if (q == null || q.isEmpty()) {
                    q = exchange.getIn().getHeader("CamelHttpQueryString", String.class);
                }
                if (q != null && !q.isEmpty()) {
                    exchange.getIn().setHeader(Exchange.HTTP_QUERY, q);
                }
            })

            .log("🚀 [PROXY] Encaminhando para: ${header.TargetUrl}")

            // Limpa headers que podem confundir o componente HTTP de destino
            .removeHeader("CamelHttpPath")
            .removeHeader("CamelHttpQueryString")

            .toD("${header.TargetUrl}?bridgeEndpoint=true&throwExceptionOnFailure=false&httpClient.connectTimeout=5000&httpClient.responseTimeout="
                + this.httpResponseTimeoutMs)

            .convertBodyTo(String.class)

            .process(exchange -> {
                exchange.setProperty("safeResponse", RouteHelper.mascararDadosSensiveis(exchange.getIn().getBody(String.class)));
            })

            .log("🔙 [RESPOSTA] Status: ${header.CamelHttpResponseCode} de " + this.nomeServico)
            .log("📦 [BODY RESPOSTA]: ${exchangeProperty.safeResponse}")
            .setHeader("Content-Type", constant("application/json"))

            .process(exchange -> org.slf4j.MDC.remove("correlationId"));
    }

    protected void configurarServico(String nomeServico) {
        this.nomeServico = nomeServico.toLowerCase();
    }

    protected void configurarUrlDestino(String urlDestino) {
        this.urlDestino = urlDestino;
    }

    protected void configurarHttpResponseTimeoutMs(int timeoutMs) {
        this.httpResponseTimeoutMs = timeoutMs;
    }

    protected void adicionarRota(RoutePath path) {
        this.listaPath.add(path);
    }

    @Override
    public void configure() {

        this.configurarTratamentoExecao();
        this.listaPath.forEach(this::configurarRota);

    }

}
