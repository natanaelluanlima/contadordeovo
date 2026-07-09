package br.com.gruponeural.application.usecase.screen.usuario;

import br.com.gruponeural.dto.usuario.UsuarioCadastrarRequest;
import br.com.gruponeural.dto.usuario.UsuarioCadastrarResponse;
import io.smallrye.mutiny.Uni;

public interface UsuarioScreenCadastrarUseCase {

    Uni<UsuarioCadastrarResponse> cadastrar(UsuarioCadastrarRequest request);
}
