package br.com.gruponeural.dto.usuario;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class UsuarioAlterarRequest {

    private String id;
    private String descricao;
    private String usuario;
    private String senha;

}

