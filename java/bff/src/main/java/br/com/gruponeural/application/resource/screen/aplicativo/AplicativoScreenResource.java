package br.com.gruponeural.application.resource.screen.aplicativo;

import br.com.gruponeural.dto.aplicativo.AplicativoAlterarRequest;
import br.com.gruponeural.dto.aplicativo.AplicativoAlterarResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoCadastrarRequest;
import br.com.gruponeural.dto.aplicativo.AplicativoCadastrarResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoExcluirResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoListarResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoObterResponse;
import io.smallrye.mutiny.Uni;

public interface AplicativoScreenResource {

    Uni<AplicativoListarResponse> listar(Integer pageNumber, Integer pageSize);

    Uni<AplicativoCadastrarResponse> cadastrar(AplicativoCadastrarRequest request);

    Uni<AplicativoObterResponse> obter(String id);

    Uni<AplicativoAlterarResponse> alterar(String id, AplicativoAlterarRequest request);

    Uni<AplicativoExcluirResponse> excluir(String id);
}

