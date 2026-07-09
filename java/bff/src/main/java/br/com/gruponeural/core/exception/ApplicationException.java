package br.com.gruponeural.core.exception;

import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import br.com.gruponeural.core.log.LogUtil;
import jakarta.ws.rs.core.Response.Status;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ApplicationException
    extends RuntimeException {

    private final Status codigoHttp;
    private ExceptionMesangemTipoEnum mensagemTipo;
    private String mensagemTitulo;
    private String mensagemDetalhe;

    public ApplicationException(Status codigoHttp, ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        super(mensagemDetalhe);

        this.codigoHttp = codigoHttp;
        this.mensagemTipo = mensagemTipo;
        this.mensagemTitulo = mensagemTitulo;
        this.mensagemDetalhe = mensagemDetalhe;

        LogUtil
            .error()
            .setClass(this.getClass())
            .setMethodName("ApplicationException")
            .setValuesName("codigoHttp", "mensagemTipo", "mensagemTitulo", "mensagemDetalhe")
            .setValues(codigoHttp, mensagemTipo, mensagemTitulo, mensagemDetalhe)
            .build();

    }

    public ApplicationException(Status codigoHttp, ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe, Throwable causa) {

        super(mensagemDetalhe, causa);

        this.codigoHttp = codigoHttp;
        this.mensagemTipo = mensagemTipo;
        this.mensagemTitulo = mensagemTitulo;
        this.mensagemDetalhe = mensagemDetalhe;

        LogUtil
            .error()
            .setClass(this.getClass())
            .setMethodName("ApplicationException")
            .setValuesName("codigoHttp", "mensagemTipo", "mensagemTitulo", "mensagemDetalhe")
            .setValues(codigoHttp, mensagemTipo, mensagemTitulo, mensagemDetalhe)
            .setThrowable(causa)
            .build();

    }

}
