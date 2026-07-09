package br.com.gruponeural.application.usecase.screen.usuario;

import br.com.gruponeural.dto.usuario.UsuarioExcluirResponse;
import io.smallrye.mutiny.Uni;

public interface UsuarioScreenExcluirUseCase {

    Uni<UsuarioExcluirResponse> excluir(String id);
}
