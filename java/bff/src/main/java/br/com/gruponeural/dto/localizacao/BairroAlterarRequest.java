package br.com.gruponeural.dto.localizacao;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class BairroAlterarRequest {

    private String idCidade;
    private String descricao;
}
