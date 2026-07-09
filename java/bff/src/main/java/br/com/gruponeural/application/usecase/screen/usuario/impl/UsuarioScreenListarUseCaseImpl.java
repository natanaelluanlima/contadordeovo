package br.com.gruponeural.application.usecase.screen.usuario.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.usuario.UsuarioScreenListarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.usuario.UsuarioListarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.UsuarioCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class UsuarioScreenListarUseCaseImpl implements UsuarioScreenListarUseCase {

    @Inject
    @RestClient
    UsuarioCortexRestClient usuarioCortexRestClient;

    @Override
    public Uni<UsuarioListarResponse> listar(Integer pageNumber, Integer pageSize) {
        return usuarioCortexRestClient
            .listar(pageNumber, pageSize)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setValuesName("usuarioListarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setThrowable(throwable)
                .setText("Erro ao listar usuários no Cortex")
                .build());
    }
}
