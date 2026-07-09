package br.com.gruponeural.dto.common;

import java.util.UUID;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ClienteDTO {

    private UUID id;
    private String nome;
    private String dataHoraCadastro;
    private String dataHoraExclusao;
}

