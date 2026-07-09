package br.com.gruponeural.application.resource.screen.empresa;

import java.util.UUID;

import br.com.gruponeural.dto.response.screen.empresa.EmpresaScreenObterResponse;
import io.smallrye.mutiny.Uni;

public interface EmpresaScreenResource {

    Uni<EmpresaScreenObterResponse> obter(UUID idOrganizacao);

}
