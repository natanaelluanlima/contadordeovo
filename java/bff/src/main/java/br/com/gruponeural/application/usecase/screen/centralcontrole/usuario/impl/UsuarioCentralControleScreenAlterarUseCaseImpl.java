package br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.UsuarioCentralControleScreenAlterarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.usuario.UsuarioAlterarRequest;
import br.com.gruponeural.dto.usuario.UsuarioAlterarResponse;
import br.com.gruponeural.infrastructure.restclient.centralcontrole.UsuarioCentralControleApiRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class UsuarioCentralControleScreenAlterarUseCaseImpl implements UsuarioCentralControleScreenAlterarUseCase {

    @Inject
    @RestClient
    UsuarioCentralControleApiRestClient usuarioCentralControleApiRestClient;

    @Override
    public Uni<UsuarioAlterarResponse> alterar(String id, UsuarioAlterarRequest request) {
        return usuarioCentralControleApiRestClient
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
                .setText("Erro ao alterar usuário no Central de Controle")
                .build());
    }
}
