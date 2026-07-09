package br.com.gruponeural.application.usecase.screen.localizacao.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenCadastrarBairroUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.localizacao.BairroCadastrarRequest;
import br.com.gruponeural.dto.localizacao.LocalizacaoItemDTO;
import br.com.gruponeural.infrastructure.restclient.cortex.localizacao.LocalizacaoRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class LocalizacaoScreenCadastrarBairroUseCaseImpl implements LocalizacaoScreenCadastrarBairroUseCase {

    @Inject
    @RestClient
    LocalizacaoRestClient localizacaoRestClient;

    @Override
    public Uni<LocalizacaoItemDTO> cadastrar(String idCidade, BairroCadastrarRequest request) {
        return localizacaoRestClient
            .cadastrarBairro(idCidade, request)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setValuesName("localizacaoBairro")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setThrowable(throwable)
                .setText("Erro ao cadastrar bairro no MS Localizacao")
                .build());
    }
}
