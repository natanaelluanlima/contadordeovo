package br.com.gruponeural.application.usecase.screen.liberacao;

import br.com.gruponeural.dto.liberacao.LiberacaoExcluirResponse;
import io.smallrye.mutiny.Uni;

public interface LiberacaoScreenExcluirUseCase {

    Uni<LiberacaoExcluirResponse> excluir(String id);
}

