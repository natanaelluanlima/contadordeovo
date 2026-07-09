package br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.UsuarioCentralControleScreenCadastrarUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.usuario.UsuarioCadastrarRequest;
import br.com.gruponeural.dto.usuario.UsuarioCadastrarResponse;
import br.com.gruponeural.infrastructure.restclient.centralcontrole.UsuarioCentralControleApiRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class UsuarioCentralControleScreenCadastrarUseCaseImpl implements UsuarioCentralControleScreenCadastrarUseCase {

    @Inject
    @RestClient
    UsuarioCentralControleApiRestClient usuarioCentralControleApiRestClient;

    @Override
    public Uni<UsuarioCadastrarResponse> cadastrar(UsuarioCadastrarRequest request) {
        return usuarioCentralControleApiRestClient
            .cadastrar(request)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setValuesName("usuarioCadastrarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setThrowable(throwable)
                .setText("Erro ao cadastrar usuário no Central de Controle")
                .build());
    }
}
