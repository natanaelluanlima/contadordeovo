package br.com.gruponeural.application.usecase.screen.liberacao.impl;

import java.util.UUID;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.liberacao.LiberacaoScreenAlterarUseCase;
import br.com.gruponeural.core.constant.AplicativoConst;
import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import br.com.gruponeural.core.exception.BadRequestException;
import br.com.gruponeural.core.mapper.DownstreamErrorPropagation;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.liberacao.LiberacaoAlterarRequest;
import br.com.gruponeural.dto.liberacao.LiberacaoAlterarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.ClienteCortexRestClient;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.LiberacaoCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.ws.rs.WebApplicationException;
import jakarta.ws.rs.core.Response;

@ApplicationScoped
public class LiberacaoScreenAlterarUseCaseImpl implements LiberacaoScreenAlterarUseCase {

    @Inject
    @RestClient
    LiberacaoCortexRestClient liberacaoCortexRestClient;

    @Inject
    @RestClient
    ClienteCortexRestClient clienteCortexRestClient;

    @Override
    public Uni<LiberacaoAlterarResponse> alterar(String id, LiberacaoAlterarRequest request) {
        return Uni.createFrom()
            .item(request)
            .map(req -> validarECompletarRequest(id, req))
            .chain(this::validarClienteExisteSeInformado)
            .chain(req -> liberacaoCortexRestClient.alterar(id, req))
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setValuesName("liberacaoAlterarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setThrowable(throwable)
                .setText("Erro ao alterar liberação no Cortex")
                .build());
    }

    private Uni<LiberacaoAlterarRequest> validarClienteExisteSeInformado(LiberacaoAlterarRequest request) {
        String idCliente = request.getIdCliente() == null ? null : request.getIdCliente().trim();
        if (idCliente == null || idCliente.isEmpty()) {
            return Uni.createFrom().item(request);
        }

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

    private static LiberacaoAlterarRequest validarECompletarRequest(String id, LiberacaoAlterarRequest request) {
        if (id == null || id.trim().isEmpty()) {
            throw new BadRequestException(
                ExceptionMesangemTipoEnum.FALHA,
                "Requisição inválida",
                "Informe o id da liberação.");
        }

        try {
            UUID.fromString(id.trim());
        } catch (IllegalArgumentException e) {
            throw new BadRequestException(
                ExceptionMesangemTipoEnum.FALHA,
                "Requisição inválida",
                "O id da liberação deve ser um UUID válido.");
        }

        if (request == null) {
            request = new LiberacaoAlterarRequest();
        }

        if (request.getIdCliente() != null && !request.getIdCliente().trim().isEmpty()) {
            try {
                UUID.fromString(request.getIdCliente().trim());
            } catch (IllegalArgumentException e) {
                throw new BadRequestException(
                    ExceptionMesangemTipoEnum.FALHA,
                    "Requisição inválida",
                    "O idCliente deve ser um UUID válido.");
            }
        }

        request.setIdAplicativo(AplicativoConst.APROVEITE_MAIS.getId().toString());
        request.setId(id.trim());
        return request;
    }
}

