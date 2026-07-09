package br.com.gruponeural.dto.usuario;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class UsuarioCadastrarRequest {

    private String descricao;
    private String usuario;
    private String senha;

}

