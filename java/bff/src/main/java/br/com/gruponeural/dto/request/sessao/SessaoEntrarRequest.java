package br.com.gruponeural.dto.request.sessao;

import java.util.UUID;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class SessaoEntrarRequest {

    /**
     * Mesmo contrato do Cortex Sessão ({@code SessaoEntrarRequest} do MS): basta para entrar.
     * Pode ser omitido se {@link #dispositivo}{@code .obrigatorio.id} estiver preenchido.
     */
    private UUID idDispositivo;

    private String nomeUsuario;
    private String senha;

    /**
     * Quando informado (com {@code obrigatorio}), após o login o BFF chama {@code dispositivo/v1/atualizar}.
     */
    private SessaoEntrarDispositivoRequest dispositivo;

}
