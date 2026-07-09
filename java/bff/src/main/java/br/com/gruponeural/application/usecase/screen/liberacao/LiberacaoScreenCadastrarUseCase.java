package br.com.gruponeural.application.usecase.screen.liberacao;

import br.com.gruponeural.dto.liberacao.LiberacaoCadastrarRequest;
import br.com.gruponeural.dto.liberacao.LiberacaoCadastrarResponse;
import io.smallrye.mutiny.Uni;

public interface LiberacaoScreenCadastrarUseCase {

    Uni<LiberacaoCadastrarResponse> cadastrar(LiberacaoCadastrarRequest request);
}

