package br.com.gruponeural.application.usecase.screen.aplicativo;

import br.com.gruponeural.dto.aplicativo.AplicativoObterResponse;
import io.smallrye.mutiny.Uni;

public interface AplicativoScreenObterUseCase {

    Uni<AplicativoObterResponse> obter(String id);
}

