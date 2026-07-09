package br.com.gruponeural.dto.response.grupo;

import br.com.gruponeural.core.dto.response.PageResponse;
import br.com.gruponeural.dto.common.GrupoDTO;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class GrupoListarResponse {

    private PageResponse<GrupoDTO> pagina;

}
