package br.com.gruponeural.application.usecase.screen.centralcontrole.usuario;

import br.com.gruponeural.dto.usuario.UsuarioExcluirResponse;
import io.smallrye.mutiny.Uni;

public interface UsuarioCentralControleScreenExcluirUseCase {

    Uni<UsuarioExcluirResponse> excluir(String id);
}
