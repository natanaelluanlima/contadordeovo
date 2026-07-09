package br.com.gruponeural.application.usecase.screen.liberacao;

import br.com.gruponeural.dto.liberacao.LiberacaoObterResponse;
import io.smallrye.mutiny.Uni;

public interface LiberacaoScreenObterUseCase {

    Uni<LiberacaoObterResponse> obter(String id);
}

