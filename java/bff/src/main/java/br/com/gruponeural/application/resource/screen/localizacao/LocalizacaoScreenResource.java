package br.com.gruponeural.application.resource.screen.localizacao;

import java.util.List;

import br.com.gruponeural.dto.localizacao.BairroAlterarRequest;
import br.com.gruponeural.dto.localizacao.BairroCadastrarRequest;
import br.com.gruponeural.dto.localizacao.BairroExcluirResponse;
import br.com.gruponeural.dto.localizacao.BairroObterResponse;
import br.com.gruponeural.dto.localizacao.LocalizacaoItemDTO;
import io.smallrye.mutiny.Uni;

public interface LocalizacaoScreenResource {

    Uni<List<LocalizacaoItemDTO>> listarEstados();

    Uni<List<LocalizacaoItemDTO>> listarCidades(String idEstado);

    Uni<List<LocalizacaoItemDTO>> listarBairros(String idCidade);

    Uni<LocalizacaoItemDTO> cadastrarBairro(String idCidade, BairroCadastrarRequest request);

    Uni<BairroObterResponse> obterBairro(String id);

    Uni<LocalizacaoItemDTO> alterarBairro(String id, BairroAlterarRequest request);

    Uni<BairroExcluirResponse> excluirBairro(String id);
}
