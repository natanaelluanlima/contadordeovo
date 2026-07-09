package br.com.gruponeural.core.dto.response;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ExceptionResponse {

    private String mensagemTipo;
    private String mensagemTitulo;
    private String mensagemDetalhe;

    public ExceptionResponse(String mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        this.mensagemTipo = mensagemTipo;
        this.mensagemTitulo = mensagemTitulo;
        this.mensagemDetalhe = mensagemDetalhe;

    }

}
