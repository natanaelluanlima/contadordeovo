package br.com.gruponeural.application.usecase.screen.localizacao.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenExcluirBairroUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.localizacao.BairroExcluirResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.localizacao.LocalizacaoRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class LocalizacaoScreenExcluirBairroUseCaseImpl implements LocalizacaoScreenExcluirBairroUseCase {

    @Inject
    @RestClient
    LocalizacaoRestClient localizacaoRestClient;

    @Override
    public Uni<BairroExcluirResponse> excluir(String id) {
        return localizacaoRestClient
            .excluirBairro(id)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("excluir")
                .setValuesName("localizacaoBairro")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("excluir")
                .setThrowable(throwable)
                .setText("Erro ao excluir bairro no MS Localizacao")
                .build());
    }
}
