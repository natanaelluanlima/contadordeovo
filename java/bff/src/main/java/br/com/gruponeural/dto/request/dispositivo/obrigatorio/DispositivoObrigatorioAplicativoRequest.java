package br.com.gruponeural.dto.request.dispositivo.obrigatorio;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class DispositivoObrigatorioAplicativoRequest {

    private String nome;
    private String versao;
    private String projetoId;
    private String orientacao;
    private String estiloInterface;

}
