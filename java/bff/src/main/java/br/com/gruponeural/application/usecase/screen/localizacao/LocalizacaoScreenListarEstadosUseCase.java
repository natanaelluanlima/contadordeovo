package br.com.gruponeural.application.usecase.screen.localizacao;

import java.util.List;

import br.com.gruponeural.dto.localizacao.LocalizacaoItemDTO;
import io.smallrye.mutiny.Uni;

public interface LocalizacaoScreenListarEstadosUseCase {

    Uni<List<LocalizacaoItemDTO>> listar();
}
