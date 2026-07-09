package br.com.gruponeural.dto.aplicativo;

import br.com.gruponeural.core.dto.response.PageResponse;
import br.com.gruponeural.dto.common.AplicativoDTO;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class AplicativoListarResponse {

    private PageResponse<AplicativoDTO> pagina;
}

