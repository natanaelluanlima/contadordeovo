package br.com.gruponeural.application.usecase.screen.usuario.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.usuario.UsuarioScreenObterUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.usuario.UsuarioObterResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.UsuarioCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class UsuarioScreenObterUseCaseImpl implements UsuarioScreenObterUseCase {

    @Inject
    @RestClient
    UsuarioCortexRestClient usuarioCortexRestClient;

    @Override
    public Uni<UsuarioObterResponse> obter(String id) {
        return usuarioCortexRestClient
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
                .setText("Erro ao obter usuário no Cortex")
                .build());
    }
}
