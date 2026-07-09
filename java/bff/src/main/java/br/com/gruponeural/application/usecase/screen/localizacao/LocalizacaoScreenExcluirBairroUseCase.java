package br.com.gruponeural.application.usecase.screen.localizacao;

import br.com.gruponeural.dto.localizacao.BairroExcluirResponse;
import io.smallrye.mutiny.Uni;

public interface LocalizacaoScreenExcluirBairroUseCase {

    Uni<BairroExcluirResponse> excluir(String id);
}
