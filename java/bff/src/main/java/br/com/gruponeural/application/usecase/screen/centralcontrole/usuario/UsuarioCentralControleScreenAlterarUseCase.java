package br.com.gruponeural.application.usecase.screen.centralcontrole.usuario;

import br.com.gruponeural.dto.usuario.UsuarioAlterarRequest;
import br.com.gruponeural.dto.usuario.UsuarioAlterarResponse;
import io.smallrye.mutiny.Uni;

public interface UsuarioCentralControleScreenAlterarUseCase {

    Uni<UsuarioAlterarResponse> alterar(String id, UsuarioAlterarRequest request);
}
