package br.com.gruponeural.core.builder.enumerator;

import lombok.Getter;

@Getter
public enum SQLOperadorEnum {

    IGUAL("="),
    DIFERENTE("<>"),
    MAIOR_QUE(">"),
    MENOR_QUE("<"),
    NULO("is null"),
    NAO_NULO("is not null");

    private final String operador;

    SQLOperadorEnum(String operador) {

        this.operador = operador;
        
    }
    
}