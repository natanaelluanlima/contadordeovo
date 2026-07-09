package br.com.gruponeural.application.usecase.screen.aplicativo;

import br.com.gruponeural.dto.aplicativo.AplicativoAlterarRequest;
import br.com.gruponeural.dto.aplicativo.AplicativoAlterarResponse;
import io.smallrye.mutiny.Uni;

public interface AplicativoScreenAlterarUseCase {

    Uni<AplicativoAlterarResponse> alterar(String id, AplicativoAlterarRequest request);
}

