package br.com.gruponeural.dto.response.screen.empresa;

import br.com.gruponeural.core.dto.response.PageResponse;
import br.com.gruponeural.dto.common.GrupoDTO;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class EmpresaScreenObterResponse {

    private PageResponse<GrupoDTO> paginaGrupo;

}
