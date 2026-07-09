package br.com.gruponeural.application.usecase.screen.cliente.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.cliente.ClienteScreenListarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.cliente.ClienteListarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.ClienteCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class ClienteScreenListarUseCaseImpl implements ClienteScreenListarUseCase {

    @Inject
    @RestClient
    ClienteCortexRestClient clienteCortexRestClient;

    @Override
    public Uni<ClienteListarResponse> listar(Integer pageNumber, Integer pageSize) {
        return clienteCortexRestClient
            .listar(pageNumber, pageSize)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setValuesName("clienteListarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setThrowable(throwable)
                .setText("Erro ao listar clientes no Cortex")
                .build());
    }
}

