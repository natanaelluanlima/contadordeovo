package br.com.gruponeural.application.usecase.screen.localizacao.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenObterBairroUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.localizacao.BairroObterResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.localizacao.LocalizacaoRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class LocalizacaoScreenObterBairroUseCaseImpl implements LocalizacaoScreenObterBairroUseCase {

    @Inject
    @RestClient
    LocalizacaoRestClient localizacaoRestClient;

    @Override
    public Uni<BairroObterResponse> obter(String id) {
        return localizacaoRestClient
            .obterBairro(id)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setValuesName("localizacaoBairro")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setThrowable(throwable)
                .setText("Erro ao obter bairro no MS Localizacao")
                .build());
    }
}
