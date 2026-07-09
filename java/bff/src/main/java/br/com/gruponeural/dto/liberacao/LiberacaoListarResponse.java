package br.com.gruponeural.dto.liberacao;

import br.com.gruponeural.core.dto.response.PageResponse;
import br.com.gruponeural.dto.common.LiberacaoDTO;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class LiberacaoListarResponse {

    private PageResponse<LiberacaoDTO> pagina;
}

