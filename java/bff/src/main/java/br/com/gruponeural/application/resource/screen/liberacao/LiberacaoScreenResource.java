package br.com.gruponeural.application.resource.screen.liberacao;

import br.com.gruponeural.dto.liberacao.LiberacaoAlterarRequest;
import br.com.gruponeural.dto.liberacao.LiberacaoAlterarResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoCadastrarRequest;
import br.com.gruponeural.dto.liberacao.LiberacaoCadastrarResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoExcluirResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoListarResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoObterResponse;
import io.smallrye.mutiny.Uni;

public interface LiberacaoScreenResource {

    Uni<LiberacaoListarResponse> listar(Integer pageNumber, Integer pageSize);

    Uni<LiberacaoCadastrarResponse> cadastrar(LiberacaoCadastrarRequest request);

    Uni<LiberacaoObterResponse> obter(String id);

    Uni<LiberacaoAlterarResponse> alterar(String id, LiberacaoAlterarRequest request);

    Uni<LiberacaoExcluirResponse> excluir(String id);
}

