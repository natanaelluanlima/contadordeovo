package br.com.gruponeural.core.enumerator;

import lombok.Getter;

@Getter
public enum ExceptionMesangemTipoEnum {

    SUCESSO("sucesso"),
    AVISO("aviso"),
    FALHA("falha");

    private String tipo;

    ExceptionMesangemTipoEnum(String tipo) {

        this.tipo = tipo;

    }

}
