package br.com.gruponeural.application.usecase.screen.aplicativo.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.aplicativo.AplicativoScreenListarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.aplicativo.AplicativoListarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.AplicativoCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class AplicativoScreenListarUseCaseImpl implements AplicativoScreenListarUseCase {

    @Inject
    @RestClient
    AplicativoCortexRestClient aplicativoCortexRestClient;

    @Override
    public Uni<AplicativoListarResponse> listar(Integer pageNumber, Integer pageSize) {
        return aplicativoCortexRestClient
            .listar(pageNumber, pageSize)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setValuesName("aplicativoListarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setThrowable(throwable)
                .setText("Erro ao listar aplicativos no Cortex")
                .build());
    }
}

