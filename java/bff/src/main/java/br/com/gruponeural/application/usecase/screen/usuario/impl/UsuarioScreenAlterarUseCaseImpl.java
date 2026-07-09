package br.com.gruponeural.application.usecase.screen.usuario.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.usuario.UsuarioScreenAlterarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.usuario.UsuarioAlterarRequest;
import br.com.gruponeural.dto.usuario.UsuarioAlterarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.UsuarioCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class UsuarioScreenAlterarUseCaseImpl implements UsuarioScreenAlterarUseCase {

    @Inject
    @RestClient
    UsuarioCortexRestClient usuarioCortexRestClient;

    @Override
    public Uni<UsuarioAlterarResponse> alterar(String id, UsuarioAlterarRequest request) {
        return usuarioCortexRestClient
            .alterar(id, request)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setValuesName("usuarioAlterarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setThrowable(throwable)
                .setText("Erro ao alterar usuário no Cortex")
                .build());
    }
}
