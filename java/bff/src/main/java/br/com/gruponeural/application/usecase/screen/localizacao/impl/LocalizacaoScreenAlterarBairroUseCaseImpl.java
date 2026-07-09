package br.com.gruponeural.application.usecase.screen.localizacao.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenAlterarBairroUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.localizacao.BairroAlterarRequest;
import br.com.gruponeural.dto.localizacao.LocalizacaoItemDTO;
import br.com.gruponeural.infrastructure.restclient.cortex.localizacao.LocalizacaoRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class LocalizacaoScreenAlterarBairroUseCaseImpl implements LocalizacaoScreenAlterarBairroUseCase {

    @Inject
    @RestClient
    LocalizacaoRestClient localizacaoRestClient;

    @Override
    public Uni<LocalizacaoItemDTO> alterar(String id, BairroAlterarRequest request) {
        return localizacaoRestClient
            .alterarBairro(id, request)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setValuesName("localizacaoBairro")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setThrowable(throwable)
                .setText("Erro ao alterar bairro no MS Localizacao")
                .build());
    }
}
