package br.com.gruponeural.application.usecase.screen.sessao.impl;

import java.util.UUID;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.sessao.SessaoScreenEntrarUseCase;
import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import br.com.gruponeural.core.exception.BadRequestException;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.request.dispositivo.DispositivoAtualizarRequest;
import br.com.gruponeural.dto.request.sessao.SessaoEntrarCortexRequest;
import br.com.gruponeural.dto.request.sessao.SessaoEntrarRequest;
import br.com.gruponeural.dto.response.sessao.SessaoEntrarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.sessao.SessaoDispositivoRestClient;
import br.com.gruponeural.infrastructure.restclient.cortex.sessao.SessaoSessaoRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class SessaoScreenEntrarUseCaseImpl
    implements SessaoScreenEntrarUseCase {

    @Inject
    @RestClient
    SessaoSessaoRestClient sessaoSessaoRestClient;

    @Inject
    @RestClient
    SessaoDispositivoRestClient sessaoDispositivoRestClient;

    @Override
    public Uni<SessaoEntrarResponse> entrar(SessaoEntrarRequest request) {
        return Uni.createFrom()
            .item(request)
            .map(SessaoScreenEntrarUseCaseImpl::montarPayloadEntrarCortex)
            .chain(sessaoSessaoRestClient::entrar)
            .invoke(
                response -> LogUtil
                    .trace()
                    .setClass(this.getClass())
                    .setMethodName("entrar")
                    .setValuesName("sessaoEntrarResponse")
                    .setValues(response)
                    .build())
            .onFailure()
            .invoke(
                throwable -> LogUtil
                    .error()
                    .setClass(this.getClass())
                    .setMethodName("entrar")
                    .setThrowable(throwable)
                    .setText("Erro ao entrar na sessão no Cortex Sessão")
                    .build())
            .chain(response -> {
                if (!deveAtualizarDispositivo(request)) {
                    return Uni.createFrom().item(response);
                }
                return sessaoDispositivoRestClient
                    .atualizarDispositivo(montarDispositivoAtualizarRequest(response, request))
                    .invoke(
                        atualizarResponse -> LogUtil
                            .trace()
                            .setClass(this.getClass())
                            .setMethodName("entrar")
                            .setValuesName("dispositivoAtualizarResponse")
                            .setValues(atualizarResponse)
                            .build())
                    .onFailure()
                    .invoke(
                        throwable -> LogUtil
                            .error()
                            .setClass(this.getClass())
                            .setMethodName("entrar")
                            .setThrowable(throwable)
                            .setText("Erro ao atualizar dispositivo no Cortex Sessão após entrar")
                            .build())
                    .replaceWith(response);
            });
    }

    private static boolean deveAtualizarDispositivo(SessaoEntrarRequest request) {
        return request.getDispositivo() != null
            && request.getDispositivo().getObrigatorio() != null;
    }

    private static SessaoEntrarCortexRequest montarPayloadEntrarCortex(SessaoEntrarRequest request) {
        UUID idDispositivo = resolverIdDispositivo(request);
        if (idDispositivo == null) {
            throw new BadRequestException(
                ExceptionMesangemTipoEnum.FALHA,
                "Requisição inválida",
                "Informe idDispositivo (raiz) ou dispositivo.obrigatorio.id, além de nomeUsuario e senha.");
        }
        SessaoEntrarCortexRequest body = new SessaoEntrarCortexRequest();
        body.setIdDispositivo(idDispositivo);
        body.setNomeUsuario(request.getNomeUsuario());
        body.setSenha(request.getSenha());
        return body;
    }

    private static UUID resolverIdDispositivo(SessaoEntrarRequest request) {
        if (request.getDispositivo() != null
            && request.getDispositivo().getObrigatorio() != null
            && request.getDispositivo().getObrigatorio().getId() != null) {
            return request.getDispositivo().getObrigatorio().getId();
        }
        return request.getIdDispositivo();
    }

    private static DispositivoAtualizarRequest montarDispositivoAtualizarRequest(
        SessaoEntrarResponse sessaoEntrarResponse,
        SessaoEntrarRequest request) {

        DispositivoAtualizarRequest atualizar = new DispositivoAtualizarRequest();
        atualizar.setIdPessoa(sessaoEntrarResponse.getIdPessoa().toString());
        atualizar.setObrigatorio(request.getDispositivo().getObrigatorio());
        atualizar.setOpcional(request.getDispositivo().getOpcional());
        return atualizar;
    }

}
