package br.com.gruponeural.application.usecase.screen.usuario;

import br.com.gruponeural.dto.usuario.UsuarioObterResponse;
import io.smallrye.mutiny.Uni;

public interface UsuarioScreenObterUseCase {

    Uni<UsuarioObterResponse> obter(String id);
}
