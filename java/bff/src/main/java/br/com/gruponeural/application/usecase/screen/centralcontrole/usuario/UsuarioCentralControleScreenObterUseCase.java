package br.com.gruponeural.application.usecase.screen.centralcontrole.usuario;

import br.com.gruponeural.dto.usuario.UsuarioObterResponse;
import io.smallrye.mutiny.Uni;

public interface UsuarioCentralControleScreenObterUseCase {

    Uni<UsuarioObterResponse> obter(String id);
}
