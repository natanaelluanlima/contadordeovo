package br.com.gruponeural.core.mapper;

import br.com.gruponeural.core.dto.response.ExceptionResponse;
import br.com.gruponeural.core.exception.ApplicationException;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;

@Provider
public class ApplicationExceptionMapper
    implements ExceptionMapper<ApplicationException> {

    @Override
    public Response toResponse(ApplicationException applicationException) {

        ExceptionResponse exceptionResponse = new ExceptionResponse(
            applicationException.getMensagemTipo().getTipo(),
            applicationException.getMensagemTitulo(),
            applicationException.getMensagemDetalhe());

        return Response
            .status(applicationException.getCodigoHttp())
            .entity(exceptionResponse)
            .build();

    }
}
