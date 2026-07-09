package br.com.gruponeural.application.usecase.screen.cliente;

import br.com.gruponeural.dto.cliente.ClienteExcluirResponse;
import io.smallrye.mutiny.Uni;

public interface ClienteScreenExcluirUseCase {

    Uni<ClienteExcluirResponse> excluir(String id);
}

