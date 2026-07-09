package br.com.gruponeural.core.exception;

import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import jakarta.ws.rs.core.Response.Status;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PersistenceException
    extends ApplicationException {

    public PersistenceException(ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        super(Status.BAD_REQUEST, mensagemTipo, mensagemTitulo, mensagemDetalhe);
    }

}
