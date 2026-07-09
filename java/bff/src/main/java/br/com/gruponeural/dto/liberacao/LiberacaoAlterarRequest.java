package br.com.gruponeural.dto.liberacao;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class LiberacaoAlterarRequest {

    private String id;
    private String idAplicativo;
    private String idCliente;
    private Boolean liberado;
    private String dataValidade;
}

