package br.com.gruponeural.application.usecase.screen.cliente.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.cliente.ClienteScreenCadastrarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.cliente.ClienteCadastrarRequest;
import br.com.gruponeural.dto.cliente.ClienteCadastrarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.ClienteCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class ClienteScreenCadastrarUseCaseImpl implements ClienteScreenCadastrarUseCase {

    @Inject
    @RestClient
    ClienteCortexRestClient clienteCortexRestClient;

    @Override
    public Uni<ClienteCadastrarResponse> cadastrar(ClienteCadastrarRequest request) {
        return clienteCortexRestClient
            .cadastrar(request)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setValuesName("clienteCadastrarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setThrowable(throwable)
                .setText("Erro ao cadastrar cliente no Cortex")
                .build());
    }
}

