package br.com.gruponeural.dto.cliente;

import br.com.gruponeural.core.dto.response.PageResponse;
import br.com.gruponeural.dto.common.ClienteDTO;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ClienteListarResponse {

    private PageResponse<ClienteDTO> pagina;
}

