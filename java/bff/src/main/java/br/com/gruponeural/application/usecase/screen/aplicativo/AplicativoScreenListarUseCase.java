package br.com.gruponeural.application.usecase.screen.aplicativo;

import br.com.gruponeural.dto.aplicativo.AplicativoListarResponse;
import io.smallrye.mutiny.Uni;

public interface AplicativoScreenListarUseCase {

    Uni<AplicativoListarResponse> listar(Integer pageNumber, Integer pageSize);
}

