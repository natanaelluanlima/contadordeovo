package br.com.gruponeural.dto.response.sessao;

import java.util.UUID;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class SessaoRenovarResponse {

    private UUID idPessoa;
    private UUID idSessao;
    private String chaveAcesso;

}
