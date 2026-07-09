package br.com.gruponeural.application.usecase.screen.aplicativo;

import br.com.gruponeural.dto.aplicativo.AplicativoCadastrarRequest;
import br.com.gruponeural.dto.aplicativo.AplicativoCadastrarResponse;
import io.smallrye.mutiny.Uni;

public interface AplicativoScreenCadastrarUseCase {

    Uni<AplicativoCadastrarResponse> cadastrar(AplicativoCadastrarRequest request);
}

