package br.com.gruponeural.dto.request.dispositivo.obrigatorio;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class DispositivoObrigatorioSistemaOperacionalRequest {

    private String nome;
    private String versao;
    private String build;
    private String buildInterno;
    private Integer numeroAPI;

}
