package br.com.gruponeural.application.usecase.screen.cliente;

import br.com.gruponeural.dto.cliente.ClienteAlterarRequest;
import br.com.gruponeural.dto.cliente.ClienteAlterarResponse;
import io.smallrye.mutiny.Uni;

public interface ClienteScreenAlterarUseCase {

    Uni<ClienteAlterarResponse> alterar(String id, ClienteAlterarRequest request);
}

