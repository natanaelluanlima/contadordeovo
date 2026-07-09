package br.com.gruponeural.core.exception;

import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import jakarta.ws.rs.core.Response.Status;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class NotFoundException
    extends ApplicationException {

    public NotFoundException(ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        super(Status.NOT_FOUND, mensagemTipo, mensagemTitulo, mensagemDetalhe);
    }

}
