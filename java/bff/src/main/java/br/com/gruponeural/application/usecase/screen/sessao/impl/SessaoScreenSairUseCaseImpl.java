package br.com.gruponeural.application.usecase.screen.sessao.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.sessao.SessaoScreenSairUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.request.sessao.SessaoSairRequest;
import br.com.gruponeural.dto.response.sessao.SessaoSairResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.sessao.SessaoSessaoRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class SessaoScreenSairUseCaseImpl
    implements SessaoScreenSairUseCase {

    @Inject
    @RestClient
    SessaoSessaoRestClient sessaoSessaoRestClient;

    @Override
    public Uni<SessaoSairResponse> sair(SessaoSairRequest request) {
        return sessaoSessaoRestClient
            .sair(request)
            .invoke(
                response -> LogUtil
                    .trace()
                    .setClass(this.getClass())
                    .setMethodName("sair")
                    .setValuesName("sessaoSairResponse")
                    .setValues(response)
                    .build())
            .onFailure()
            .invoke(
                throwable -> LogUtil
                    .error()
                    .setClass(this.getClass())
                    .setMethodName("sair")
                    .setThrowable(throwable)
                    .setText("Erro ao sair da sessão no Cortex Sessão")
                    .build());
    }

}
