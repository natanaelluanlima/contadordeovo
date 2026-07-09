package br.com.gruponeural.application.usecase.screen.liberacao.impl;

import java.util.UUID;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.liberacao.LiberacaoScreenCadastrarUseCase;
import br.com.gruponeural.core.constant.AplicativoConst;
import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import br.com.gruponeural.core.exception.BadRequestException;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.core.mapper.DownstreamErrorPropagation;
import br.com.gruponeural.dto.liberacao.LiberacaoCadastrarRequest;
import br.com.gruponeural.dto.liberacao.LiberacaoCadastrarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.ClienteCortexRestClient;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.LiberacaoCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.ws.rs.WebApplicationException;
import jakarta.ws.rs.core.Response;

@ApplicationScoped
public class LiberacaoScreenCadastrarUseCaseImpl implements LiberacaoScreenCadastrarUseCase {

    @Inject
    @RestClient
    LiberacaoCortexRestClient liberacaoCortexRestClient;

    @Inject
    @RestClient
    ClienteCortexRestClient clienteCortexRestClient;

    @Override
    public Uni<LiberacaoCadastrarResponse> cadastrar(LiberacaoCadastrarRequest request) {
        return Uni.createFrom()
            .item(request)
            .map(LiberacaoScreenCadastrarUseCaseImpl::validarECompletarRequest)
            .chain(this::validarClienteExiste)
            .chain(liberacaoCortexRestClient::cadastrar)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setValuesName("liberacaoCadastrarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setThrowable(throwable)
                .setText("Erro ao cadastrar liberação no Cortex")
                .build());
    }

    private Uni<LiberacaoCadastrarRequest> validarClienteExiste(LiberacaoCadastrarRequest request) {
        String idCliente = request.getIdCliente() == null ? null : request.getIdCliente().trim();
        return clienteCortexRestClient
            .obter(idCliente)
            .replaceWith(request)
            .onFailure()
            .transform(throwable -> {
                WebApplicationException wae = DownstreamErrorPropagation.findWebApplicationInChain(throwable);
                if (wae != null && wae.getResponse() != null && wae.getResponse().getStatus() == Response.Status.NOT_FOUND.getStatusCode()) {
                    return new BadRequestException(
                        ExceptionMesangemTipoEnum.FALHA,
                        "Requisição inválida",
                        "O idCliente informado não existe.");
                }
                return throwable;
            });
    }

    private static LiberacaoCadastrarRequest validarECompletarRequest(LiberacaoCadastrarRequest request) {
        if (request == null) {
            throw new BadRequestException(
                ExceptionMesangemTipoEnum.FALHA,
                "Requisição inválida",
                "Body obrigatório.");
        }

        if (request.getIdCliente() == null || request.getIdCliente().trim().isEmpty()) {
            throw new BadRequestException(
                ExceptionMesangemTipoEnum.FALHA,
                "Requisição inválida",
                "Informe o idCliente.");
        }

        try {
            UUID.fromString(request.getIdCliente().trim());
        } catch (IllegalArgumentException e) {
            throw new BadRequestException(
                ExceptionMesangemTipoEnum.FALHA,
                "Requisição inválida",
                "O idCliente deve ser um UUID válido.");
        }

        request.setIdAplicativo(AplicativoConst.APROVEITE_MAIS.getId().toString());
        return request;
    }
}

