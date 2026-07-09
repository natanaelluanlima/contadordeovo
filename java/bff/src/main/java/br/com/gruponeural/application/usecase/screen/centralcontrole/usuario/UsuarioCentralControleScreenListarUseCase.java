package br.com.gruponeural.application.usecase.screen.centralcontrole.usuario;

import br.com.gruponeural.dto.usuario.UsuarioListarResponse;
import io.smallrye.mutiny.Uni;

public interface UsuarioCentralControleScreenListarUseCase {

    Uni<UsuarioListarResponse> listar(Integer pageNumber, Integer pageSize);
}
