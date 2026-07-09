package br.com.gruponeural.application.usecase.screen.cliente;

import br.com.gruponeural.dto.cliente.ClienteObterResponse;
import io.smallrye.mutiny.Uni;

public interface ClienteScreenObterUseCase {

    Uni<ClienteObterResponse> obter(String id);
}

