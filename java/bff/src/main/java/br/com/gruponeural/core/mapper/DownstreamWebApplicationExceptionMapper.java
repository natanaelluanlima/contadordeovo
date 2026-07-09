package br.com.gruponeural.core.mapper;

import com.fasterxml.jackson.databind.ObjectMapper;

import jakarta.annotation.Priority;
import jakarta.inject.Inject;
import jakarta.ws.rs.Priorities;
import jakarta.ws.rs.WebApplicationException;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;

/**
 * Propaga o status e o corpo JSON do microserviço (ex.: {@code ExceptionResponse})
 * quando o REST client levanta {@link WebApplicationException} (4xx/5xx), para o
 * gateway e o app receberem a mesma mensagem do MS (ex. login inválido).
 */
@Provider
@Priority(Priorities.USER)
public class DownstreamWebApplicationExceptionMapper
    implements ExceptionMapper<WebApplicationException> {

    @Inject
    ObjectMapper objectMapper;

    @Override
    public Response toResponse(WebApplicationException exception) {
        return DownstreamErrorPropagation.toResponse(exception, objectMapper);
    }
}
