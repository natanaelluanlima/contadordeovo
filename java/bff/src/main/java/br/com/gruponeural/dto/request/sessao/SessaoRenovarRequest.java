package br.com.gruponeural.dto.request.sessao;

import java.util.UUID;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class SessaoRenovarRequest {

    private UUID idDispositivo;
    private UUID idSessao;

}
