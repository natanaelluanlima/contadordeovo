package br.com.gruponeural.dto.request.sessao;

import java.util.UUID;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Corpo enviado ao Cortex Sessão em {@code POST v1/entrar} (apenas os três campos aceitos pelo MS).
 */
@Getter
@Setter
@NoArgsConstructor
public class SessaoEntrarCortexRequest {

    private UUID idDispositivo;
    private String nomeUsuario;
    private String senha;

}
