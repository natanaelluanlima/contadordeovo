package br.com.gruponeural.core.constant;

public enum SessaoConst {
    SESSAO_USUARIO("SESSAO_USUARIO");

    private final String valor; 

    SessaoConst(String valor) {
        this.valor = valor;
    }

    public String getValor() {
        return valor;
    }
}
