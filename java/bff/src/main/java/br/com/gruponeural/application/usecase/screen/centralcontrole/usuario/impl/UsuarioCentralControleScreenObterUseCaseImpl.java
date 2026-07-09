package br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.UsuarioCentralControleScreenObterUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.usuario.UsuarioObterResponse;
import br.com.gruponeural.infrastructure.restclient.centralcontrole.UsuarioCentralControleApiRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class UsuarioCentralControleScreenObterUseCaseImpl implements UsuarioCentralControleScreenObterUseCase {

    @Inject
    @RestClient
    UsuarioCentralControleApiRestClient usuarioCentralControleApiRestClient;

    @Override
    public Uni<UsuarioObterResponse> obter(String id) {
        return usuarioCentralControleApiRestClient
            .obter(id)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setValuesName("usuarioObterResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setThrowable(throwable)
                .setText("Erro ao obter usuário no Central de Controle")
                .build());
    }
}
