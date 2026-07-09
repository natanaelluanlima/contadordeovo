package br.com.gruponeural.dto.common;

import java.util.UUID;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class LiberacaoDTO {

    private UUID id;
    private UUID idAplicativo;
    private UUID idCliente;
    private String clienteNome;
    private String aplicativoDescricao;
    private Boolean liberado;
    private String dataValidade;
    private String dataHoraCadastro;
}

