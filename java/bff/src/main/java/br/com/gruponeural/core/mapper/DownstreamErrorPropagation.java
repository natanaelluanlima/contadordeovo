package br.com.gruponeural.core.mapper;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import br.com.gruponeural.core.dto.response.ExceptionResponse;
import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import jakarta.ws.rs.WebApplicationException;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * Reenvia para o HTTP do BFF a mesma resposta de erro (status + corpo) devolvida
 * pelo microserviço chamado via REST client. Lê o corpo como string primeiro —
 * o client do Quarkus costuma exigir isso para o entity ficar consistente
 * (ex.: 404/400 com {@link ExceptionResponse} em JSON).
 */
public final class DownstreamErrorPropagation {

    /** Resposta padrão quando o MS não devolve o corpo estruturado (ex. 404 vazio do REST client). */
    private static final String MENSAGEM_FALHA_SERVIDOR = "Falha no servidor.";

    private DownstreamErrorPropagation() {
    }

    private static ExceptionResponse respostaFalhaServidor() {
        return new ExceptionResponse(
            ExceptionMesangemTipoEnum.FALHA.getTipo(),
            MENSAGEM_FALHA_SERVIDOR,
            MENSAGEM_FALHA_SERVIDOR);
    }

    public static Response toResponse(WebApplicationException exception, ObjectMapper objectMapper) {
        Response r = exception.getResponse();
        if (r == null) {
            return Response
                .status(Response.Status.INTERNAL_SERVER_ERROR)
                .type(MediaType.APPLICATION_JSON)
                .entity(respostaFalhaServidor())
                .build();
        }

        int status = r.getStatus();
        if (r.getStatusInfo().getFamily() == Response.Status.Family.SUCCESSFUL) {
            return r;
        }
        if (!r.hasEntity()) {
            return Response
                .status(status)
                .type(MediaType.APPLICATION_JSON)
                .entity(respostaFalhaServidor())
                .build();
        }

        String raw;
        try {
            raw = r.readEntity(String.class);
        } catch (IllegalStateException e) {
            return Response
                .status(status)
                .type(MediaType.APPLICATION_JSON)
                .entity(respostaFalhaServidor())
                .build();
        }

        if (raw == null || raw.isBlank()) {
            return Response
                .status(status)
                .type(MediaType.APPLICATION_JSON)
                .entity(respostaFalhaServidor())
                .build();
        }

        try {
            ExceptionResponse body = objectMapper.readValue(raw, ExceptionResponse.class);
            return Response
                .status(status)
                .type(MediaType.APPLICATION_JSON)
                .entity(body)
                .build();
        } catch (JsonProcessingException e) {
            return Response
                .status(status)
                .type(MediaType.APPLICATION_JSON)
                .entity(respostaFalhaServidor())
                .build();
        }
    }

    public static WebApplicationException findWebApplicationInChain(Throwable t) {
        if (t == null) {
            return null;
        }
        if (t instanceof WebApplicationException wae) {
            return wae;
        }
        return findWebApplicationInChain(t.getCause());
    }
}
