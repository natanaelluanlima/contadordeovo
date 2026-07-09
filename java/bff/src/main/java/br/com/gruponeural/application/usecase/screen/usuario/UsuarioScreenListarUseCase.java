package br.com.gruponeural.application.usecase.screen.usuario;

import br.com.gruponeural.dto.usuario.UsuarioListarResponse;
import io.smallrye.mutiny.Uni;

public interface UsuarioScreenListarUseCase {

    Uni<UsuarioListarResponse> listar(Integer pageNumber, Integer pageSize);
}
