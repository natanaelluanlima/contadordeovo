package br.com.gruponeural.application.usecase.screen.localizacao;

import br.com.gruponeural.dto.localizacao.BairroObterResponse;
import io.smallrye.mutiny.Uni;

public interface LocalizacaoScreenObterBairroUseCase {

    Uni<BairroObterResponse> obter(String id);
}
