package br.com.gruponeural.core.exception;

import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import jakarta.ws.rs.core.Response.Status;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class BadRequestException
    extends ApplicationException {

    public BadRequestException(ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        super(Status.BAD_REQUEST, mensagemTipo, mensagemTitulo, mensagemDetalhe);
    }

}
