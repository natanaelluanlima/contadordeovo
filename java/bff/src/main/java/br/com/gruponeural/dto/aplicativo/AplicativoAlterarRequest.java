package br.com.gruponeural.dto.aplicativo;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class AplicativoAlterarRequest {

    private String id;
    private String descricao;
}

