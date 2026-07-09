package br.com.gruponeural.application.usecase.screen.usuario;

import br.com.gruponeural.dto.usuario.UsuarioAlterarRequest;
import br.com.gruponeural.dto.usuario.UsuarioAlterarResponse;
import io.smallrye.mutiny.Uni;

public interface UsuarioScreenAlterarUseCase {

    Uni<UsuarioAlterarResponse> alterar(String id, UsuarioAlterarRequest request);
}
