package br.com.gruponeural.application.usecase.screen.usuario.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.usuario.UsuarioScreenExcluirUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.usuario.UsuarioExcluirResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.UsuarioCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class UsuarioScreenExcluirUseCaseImpl implements UsuarioScreenExcluirUseCase {

    @Inject
    @RestClient
    UsuarioCortexRestClient usuarioCortexRestClient;

    @Override
    public Uni<UsuarioExcluirResponse> excluir(String id) {
        return usuarioCortexRestClient
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
                .setText("Erro ao excluir usuário no Cortex")
                .build());
    }
}
