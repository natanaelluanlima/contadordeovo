package br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.UsuarioCentralControleScreenListarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.usuario.UsuarioListarResponse;
import br.com.gruponeural.infrastructure.restclient.centralcontrole.UsuarioCentralControleApiRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class UsuarioCentralControleScreenListarUseCaseImpl implements UsuarioCentralControleScreenListarUseCase {

    @Inject
    @RestClient
    UsuarioCentralControleApiRestClient usuarioCentralControleApiRestClient;

    @Override
    public Uni<UsuarioListarResponse> listar(Integer pageNumber, Integer pageSize) {
        return usuarioCentralControleApiRestClient
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
                .setText("Erro ao listar usuários no Central de Controle")
                .build());
    }
}
