package br.com.gruponeural.core.exception;

import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import jakarta.ws.rs.core.Response.Status;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UnauthorizedException
    extends ApplicationException {

    public UnauthorizedException(ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        super(Status.UNAUTHORIZED, mensagemTipo, mensagemTitulo, mensagemDetalhe);
    }

}
