package br.com.gruponeural.dto.common;

import java.util.UUID;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class AplicativoDTO {

    private UUID id;
    private String descricao;
    private String dataHoraCadastro;
    private String dataHoraExclusao;
}

