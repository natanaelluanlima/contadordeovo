package br.com.gruponeural.application.usecase.screen.liberacao;

import br.com.gruponeural.dto.liberacao.LiberacaoAlterarRequest;
import br.com.gruponeural.dto.liberacao.LiberacaoAlterarResponse;
import io.smallrye.mutiny.Uni;

public interface LiberacaoScreenAlterarUseCase {

    Uni<LiberacaoAlterarResponse> alterar(String id, LiberacaoAlterarRequest request);
}

