package br.com.gruponeural.core.mapper;

import com.fasterxml.jackson.databind.ObjectMapper;

import br.com.gruponeural.core.dto.response.ExceptionResponse;
import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import jakarta.annotation.Priority;
import jakarta.inject.Inject;
import jakarta.ws.rs.Priorities;
import jakarta.ws.rs.ProcessingException;
import jakarta.ws.rs.WebApplicationException;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;

/**
 * Em chamadas reativas, o client por vezes envolve o erro de rede/HTTP
 * em {@link ProcessingException} com {@link WebApplicationException} (ou
 * subclasse) na cadeia de causas. Desembalamos e reutilizam a propagação do corpo.
 */
@Provider
@Priority(Priorities.USER)
public class DownstreamProcessingExceptionMapper
    implements ExceptionMapper<ProcessingException> {

    @Inject
    ObjectMapper objectMapper;

    @Override
    public Response toResponse(ProcessingException exception) {
        WebApplicationException wae = DownstreamErrorPropagation.findWebApplicationInChain(exception);
        if (wae != null) {
            return DownstreamErrorPropagation.toResponse(wae, objectMapper);
        }
        return Response
            .status(Response.Status.INTERNAL_SERVER_ERROR)
            .type(MediaType.APPLICATION_JSON)
            .entity(new ExceptionResponse(
                ExceptionMesangemTipoEnum.FALHA.getTipo(),
                "Falha no servidor.",
                "Falha no servidor."))
            .build();
    }
}
