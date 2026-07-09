package br.com.gruponeural.application.usecase.screen.aplicativo;

import br.com.gruponeural.dto.aplicativo.AplicativoExcluirResponse;
import io.smallrye.mutiny.Uni;

public interface AplicativoScreenExcluirUseCase {

    Uni<AplicativoExcluirResponse> excluir(String id);
}

