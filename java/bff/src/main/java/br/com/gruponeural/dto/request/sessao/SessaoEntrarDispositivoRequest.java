package br.com.gruponeural.dto.request.sessao;

import br.com.gruponeural.dto.request.dispositivo.obrigatorio.DispositivoObrigatorioRequest;
import br.com.gruponeural.dto.request.dispositivo.opcional.DispositivoOpcionalRequest;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class SessaoEntrarDispositivoRequest {

    private DispositivoObrigatorioRequest obrigatorio;
    private DispositivoOpcionalRequest opcional;

}
