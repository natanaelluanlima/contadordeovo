package br.com.gruponeural.application.usecase.screen.liberacao.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.liberacao.LiberacaoScreenExcluirUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.liberacao.LiberacaoExcluirResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.LiberacaoCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class LiberacaoScreenExcluirUseCaseImpl implements LiberacaoScreenExcluirUseCase {

    @Inject
    @RestClient
    LiberacaoCortexRestClient liberacaoCortexRestClient;

    @Override
    public Uni<LiberacaoExcluirResponse> excluir(String id) {
        return liberacaoCortexRestClient
            .excluir(id)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("excluir")
                .setValuesName("liberacaoExcluirResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("excluir")
                .setThrowable(throwable)
                .setText("Erro ao excluir liberação no Cortex")
                .build());
    }
}

