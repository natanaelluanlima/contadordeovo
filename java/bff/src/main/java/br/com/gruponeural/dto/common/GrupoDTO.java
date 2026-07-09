package br.com.gruponeural.dto.common;

import java.util.List;
import java.util.UUID;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class GrupoDTO {

    private UUID id;
    private String nome;
    private String descricao;
    private String dataCriacao;
    private String dataAtualizacao;
    private List<UnidadeDTO> listaUnidade;

}
