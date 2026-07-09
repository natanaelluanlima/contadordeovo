package br.com.gruponeural.application.usecase.screen.aplicativo.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.aplicativo.AplicativoScreenObterUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.aplicativo.AplicativoObterResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.AplicativoCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class AplicativoScreenObterUseCaseImpl implements AplicativoScreenObterUseCase {

    @Inject
    @RestClient
    AplicativoCortexRestClient aplicativoCortexRestClient;

    @Override
    public Uni<AplicativoObterResponse> obter(String id) {
        return aplicativoCortexRestClient
            .obter(id)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setValuesName("aplicativoObterResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setThrowable(throwable)
                .setText("Erro ao obter aplicativo no Cortex")
                .build());
    }
}

