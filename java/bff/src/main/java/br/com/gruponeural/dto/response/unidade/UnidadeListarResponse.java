package br.com.gruponeural.dto.response.unidade;

import br.com.gruponeural.core.dto.response.PageResponse;
import br.com.gruponeural.dto.common.UnidadeDTO;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class UnidadeListarResponse {

    private PageResponse<UnidadeDTO> pagina;

}
