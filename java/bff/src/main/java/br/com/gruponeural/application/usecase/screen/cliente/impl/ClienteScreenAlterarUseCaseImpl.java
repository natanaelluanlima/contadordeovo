package br.com.gruponeural.application.usecase.screen.cliente.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.cliente.ClienteScreenAlterarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.cliente.ClienteAlterarRequest;
import br.com.gruponeural.dto.cliente.ClienteAlterarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.ClienteCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class ClienteScreenAlterarUseCaseImpl implements ClienteScreenAlterarUseCase {

    @Inject
    @RestClient
    ClienteCortexRestClient clienteCortexRestClient;

    @Override
    public Uni<ClienteAlterarResponse> alterar(String id, ClienteAlterarRequest request) {
        return clienteCortexRestClient
            .alterar(id, request)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setValuesName("clienteAlterarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setThrowable(throwable)
                .setText("Erro ao alterar cliente no Cortex")
                .build());
    }
}

