package br.com.gruponeural.dto.localizacao;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class LocalizacaoItemDTO {

    private String id;
    private String descricao;
    private String sigla;
}
