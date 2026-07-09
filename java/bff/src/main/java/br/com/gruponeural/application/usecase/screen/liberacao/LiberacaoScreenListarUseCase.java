package br.com.gruponeural.application.usecase.screen.liberacao;

import br.com.gruponeural.dto.liberacao.LiberacaoListarResponse;
import io.smallrye.mutiny.Uni;

public interface LiberacaoScreenListarUseCase {

    Uni<LiberacaoListarResponse> listar(Integer pageNumber, Integer pageSize);
}

