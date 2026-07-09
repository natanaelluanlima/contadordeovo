package br.com.gruponeural.dto.common;

import java.util.UUID;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class UsuarioDTO {

    private UUID id;
    private String descricao;
    private String usuario;
    private String dataHoraCadastro;
    private String dataHoraExclusao;

}
