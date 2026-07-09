package br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.UsuarioCentralControleScreenExcluirUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.usuario.UsuarioExcluirResponse;
import br.com.gruponeural.infrastructure.restclient.centralcontrole.UsuarioCentralControleApiRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class UsuarioCentralControleScreenExcluirUseCaseImpl implements UsuarioCentralControleScreenExcluirUseCase {

    @Inject
    @RestClient
    UsuarioCentralControleApiRestClient usuarioCentralControleApiRestClient;

    @Override
    public Uni<UsuarioExcluirResponse> excluir(String id) {
        return usuarioCentralControleApiRestClient
            .excluir(id)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("excluir")
                .setValuesName("usuarioExcluirResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("excluir")
                .setThrowable(throwable)
                .setText("Erro ao excluir usuário no Central de Controle")
                .build());
    }
}
