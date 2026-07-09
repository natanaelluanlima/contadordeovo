package br.com.gruponeural.application.resource.screen.cliente;

import br.com.gruponeural.dto.cliente.ClienteAlterarRequest;
import br.com.gruponeural.dto.cliente.ClienteAlterarResponse;
import br.com.gruponeural.dto.cliente.ClienteCadastrarRequest;
import br.com.gruponeural.dto.cliente.ClienteCadastrarResponse;
import br.com.gruponeural.dto.cliente.ClienteExcluirResponse;
import br.com.gruponeural.dto.cliente.ClienteListarResponse;
import br.com.gruponeural.dto.cliente.ClienteObterResponse;
import io.smallrye.mutiny.Uni;

public interface ClienteScreenResource {

    Uni<ClienteListarResponse> listar(Integer pageNumber, Integer pageSize);

    Uni<ClienteCadastrarResponse> cadastrar(ClienteCadastrarRequest request);

    Uni<ClienteObterResponse> obter(String id);

    Uni<ClienteAlterarResponse> alterar(String id, ClienteAlterarRequest request);

    Uni<ClienteExcluirResponse> excluir(String id);
}

