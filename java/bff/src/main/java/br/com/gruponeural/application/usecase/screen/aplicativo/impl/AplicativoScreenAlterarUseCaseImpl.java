package br.com.gruponeural.application.usecase.screen.aplicativo.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.aplicativo.AplicativoScreenAlterarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.aplicativo.AplicativoAlterarRequest;
import br.com.gruponeural.dto.aplicativo.AplicativoAlterarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.AplicativoCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class AplicativoScreenAlterarUseCaseImpl implements AplicativoScreenAlterarUseCase {

    @Inject
    @RestClient
    AplicativoCortexRestClient aplicativoCortexRestClient;

    @Override
    public Uni<AplicativoAlterarResponse> alterar(String id, AplicativoAlterarRequest request) {
        if (request == null) {
            request = new AplicativoAlterarRequest();
        }
        request.setId(id);

        return aplicativoCortexRestClient
            .alterar(id, request)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setValuesName("aplicativoAlterarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setThrowable(throwable)
                .setText("Erro ao alterar aplicativo no Cortex")
                .build());
    }
}

