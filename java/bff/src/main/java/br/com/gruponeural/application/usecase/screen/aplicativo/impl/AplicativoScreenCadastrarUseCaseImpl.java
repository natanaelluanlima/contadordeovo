package br.com.gruponeural.application.usecase.screen.aplicativo.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.aplicativo.AplicativoScreenCadastrarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.aplicativo.AplicativoCadastrarRequest;
import br.com.gruponeural.dto.aplicativo.AplicativoCadastrarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.AplicativoCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class AplicativoScreenCadastrarUseCaseImpl implements AplicativoScreenCadastrarUseCase {

    @Inject
    @RestClient
    AplicativoCortexRestClient aplicativoCortexRestClient;

    @Override
    public Uni<AplicativoCadastrarResponse> cadastrar(AplicativoCadastrarRequest request) {
        return aplicativoCortexRestClient
            .cadastrar(request)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setValuesName("aplicativoCadastrarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setThrowable(throwable)
                .setText("Erro ao cadastrar aplicativo no Cortex")
                .build());
    }
}

