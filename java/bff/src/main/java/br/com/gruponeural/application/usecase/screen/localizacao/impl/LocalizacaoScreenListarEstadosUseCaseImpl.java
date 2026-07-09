package br.com.gruponeural.application.usecase.screen.localizacao.impl;

import java.util.List;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenListarEstadosUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.localizacao.LocalizacaoItemDTO;
import br.com.gruponeural.infrastructure.restclient.cortex.localizacao.LocalizacaoRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class LocalizacaoScreenListarEstadosUseCaseImpl implements LocalizacaoScreenListarEstadosUseCase {

    @Inject
    @RestClient
    LocalizacaoRestClient localizacaoRestClient;

    @Override
    public Uni<List<LocalizacaoItemDTO>> listar() {
        return localizacaoRestClient
            .listarEstados()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setValuesName("localizacaoEstados")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setThrowable(throwable)
                .setText("Erro ao listar estados no MS Localizacao")
                .build());
    }
}
