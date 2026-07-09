package br.com.gruponeural.application.usecase.screen.cliente;

import br.com.gruponeural.dto.cliente.ClienteCadastrarRequest;
import br.com.gruponeural.dto.cliente.ClienteCadastrarResponse;
import io.smallrye.mutiny.Uni;

public interface ClienteScreenCadastrarUseCase {

    Uni<ClienteCadastrarResponse> cadastrar(ClienteCadastrarRequest request);
}

