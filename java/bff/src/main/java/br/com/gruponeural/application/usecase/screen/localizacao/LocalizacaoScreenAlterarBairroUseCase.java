package br.com.gruponeural.application.usecase.screen.localizacao;

import br.com.gruponeural.dto.localizacao.BairroAlterarRequest;
import br.com.gruponeural.dto.localizacao.LocalizacaoItemDTO;
import io.smallrye.mutiny.Uni;

public interface LocalizacaoScreenAlterarBairroUseCase {

    Uni<LocalizacaoItemDTO> alterar(String id, BairroAlterarRequest request);
}
