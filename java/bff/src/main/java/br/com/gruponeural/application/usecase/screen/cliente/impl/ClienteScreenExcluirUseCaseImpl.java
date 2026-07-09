package br.com.gruponeural.application.usecase.screen.cliente.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.cliente.ClienteScreenExcluirUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.cliente.ClienteExcluirResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.ClienteCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class ClienteScreenExcluirUseCaseImpl implements ClienteScreenExcluirUseCase {

    @Inject
    @RestClient
    ClienteCortexRestClient clienteCortexRestClient;

    @Override
    public Uni<ClienteExcluirResponse> excluir(String id) {
        return clienteCortexRestClient
            .excluir(id)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("excluir")
                .setValuesName("clienteExcluirResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("excluir")
                .setThrowable(throwable)
                .setText("Erro ao excluir cliente no Cortex")
                .build());
    }
}

