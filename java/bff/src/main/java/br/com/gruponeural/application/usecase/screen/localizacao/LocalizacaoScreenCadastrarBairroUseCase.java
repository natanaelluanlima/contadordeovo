package br.com.gruponeural.application.usecase.screen.localizacao;

import br.com.gruponeural.dto.localizacao.BairroCadastrarRequest;
import br.com.gruponeural.dto.localizacao.LocalizacaoItemDTO;
import io.smallrye.mutiny.Uni;

public interface LocalizacaoScreenCadastrarBairroUseCase {

    Uni<LocalizacaoItemDTO> cadastrar(String idCidade, BairroCadastrarRequest request);
}
