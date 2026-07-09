package br.com.gruponeural.application.usecase.screen.cliente;

import br.com.gruponeural.dto.cliente.ClienteListarResponse;
import io.smallrye.mutiny.Uni;

public interface ClienteScreenListarUseCase {

    Uni<ClienteListarResponse> listar(Integer pageNumber, Integer pageSize);
}

