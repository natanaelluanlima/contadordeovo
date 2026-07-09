package br.com.gruponeural.dto.common;

import java.util.UUID;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class UnidadeDTO {

    private UUID id;
    private UUID idGrupo;
    private String nome;
    private String descricao;

}
