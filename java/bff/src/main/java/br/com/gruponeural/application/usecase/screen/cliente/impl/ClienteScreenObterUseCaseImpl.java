package br.com.gruponeural.application.usecase.screen.cliente.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.cliente.ClienteScreenObterUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.cliente.ClienteObterResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.ClienteCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class ClienteScreenObterUseCaseImpl implements ClienteScreenObterUseCase {

    @Inject
    @RestClient
    ClienteCortexRestClient clienteCortexRestClient;

    @Override
    public Uni<ClienteObterResponse> obter(String id) {
        return clienteCortexRestClient
            .obter(id)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setValuesName("clienteObterResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setThrowable(throwable)
                .setText("Erro ao obter cliente no Cortex")
                .build());
    }
}

