package br.com.gruponeural.core.builder.enumerator;

import lombok.Getter;

@Getter
public enum SQLOrdenacaoEnum {

    ASCENDENTE("asc"),
    DESCENDENTE("desc");

    private final String sentidoOrdenacao;

    SQLOrdenacaoEnum(String sentidoOrdenacao) {

        this.sentidoOrdenacao = sentidoOrdenacao;

    }

}
