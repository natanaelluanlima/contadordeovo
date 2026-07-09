package br.com.gruponeural.dto.localizacao;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class BairroObterResponse {

    private String id;
    private String idEstado;
    private String descricaoEstado;
    private String siglaEstado;
    private String idCidade;
    private String descricaoCidade;
    private String descricao;
}
