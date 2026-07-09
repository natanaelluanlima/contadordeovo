package br.com.gruponeural.dto.request.dispositivo.obrigatorio;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class DispositivoObrigatorioSegurancaRequest {

    private Integer latitude;
    private Integer longitude;
    private Integer precisaoMetros;

}
