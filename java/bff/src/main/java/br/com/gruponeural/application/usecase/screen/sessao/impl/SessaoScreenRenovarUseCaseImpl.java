package br.com.gruponeural.application.usecase.screen.sessao.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.sessao.SessaoScreenRenovarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.request.sessao.SessaoRenovarRequest;
import br.com.gruponeural.dto.response.sessao.SessaoRenovarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.sessao.SessaoSessaoRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class SessaoScreenRenovarUseCaseImpl
    implements SessaoScreenRenovarUseCase {

    @Inject
    @RestClient
    SessaoSessaoRestClient sessaoSessaoRestClient;

    @Override
    public Uni<SessaoRenovarResponse> renovar(SessaoRenovarRequest request) {
        return sessaoSessaoRestClient
            .renovar(request)
            .invoke(
                response -> LogUtil
                    .trace()
                    .setClass(this.getClass())
                    .setMethodName("renovar")
                    .setValuesName("sessaoRenovarResponse")
                    .setValues(response)
                    .build())
            .onFailure()
            .invoke(
                throwable -> LogUtil
                    .error()
                    .setClass(this.getClass())
                    .setMethodName("renovar")
                    .setThrowable(throwable)
                    .setText("Erro ao renovar sessão no Cortex Sessão")
                    .build());
    }

}
