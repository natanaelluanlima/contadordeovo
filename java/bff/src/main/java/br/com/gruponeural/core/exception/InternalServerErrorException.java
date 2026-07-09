package br.com.gruponeural.core.exception;

import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import jakarta.ws.rs.core.Response.Status;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class InternalServerErrorException
    extends ApplicationException {

    public InternalServerErrorException(ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        super(Status.INTERNAL_SERVER_ERROR, mensagemTipo, mensagemTitulo, mensagemDetalhe);
    }

}
