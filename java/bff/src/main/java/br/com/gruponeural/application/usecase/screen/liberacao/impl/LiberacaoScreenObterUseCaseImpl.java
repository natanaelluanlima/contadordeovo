package br.com.gruponeural.application.usecase.screen.liberacao.impl;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.liberacao.LiberacaoScreenObterUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.aplicativo.AplicativoObterResponse;
import br.com.gruponeural.dto.cliente.ClienteObterResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoObterResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.AplicativoCortexRestClient;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.ClienteCortexRestClient;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.LiberacaoCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class LiberacaoScreenObterUseCaseImpl implements LiberacaoScreenObterUseCase {

    @Inject
    @RestClient
    LiberacaoCortexRestClient liberacaoCortexRestClient;

    @Inject
    @RestClient
    ClienteCortexRestClient clienteCortexRestClient;

    @Inject
    @RestClient
    AplicativoCortexRestClient aplicativoCortexRestClient;

    @Override
    public Uni<LiberacaoObterResponse> obter(String id) {
        return liberacaoCortexRestClient
            .obter(id)
            .chain(this::enriquecer)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setValuesName("liberacaoObterResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setThrowable(throwable)
                .setText("Erro ao obter liberação no Cortex")
                .build());
    }

    private Uni<LiberacaoObterResponse> enriquecer(LiberacaoObterResponse response) {
        if (response == null || response.getLiberacao() == null) {
            return Uni.createFrom().item(response);
        }

        String idCliente = response.getLiberacao().getIdCliente() == null
            ? null
            : response.getLiberacao().getIdCliente().toString();
        String idAplicativo = response.getLiberacao().getIdAplicativo() == null
            ? null
            : response.getLiberacao().getIdAplicativo().toString();

        Uni<ClienteObterResponse> clienteUni = idCliente == null
            ? Uni.createFrom().nullItem()
            : clienteCortexRestClient.obter(idCliente).onFailure().recoverWithNull();

        Uni<AplicativoObterResponse> appUni = idAplicativo == null
            ? Uni.createFrom().nullItem()
            : aplicativoCortexRestClient.obter(idAplicativo).onFailure().recoverWithNull();

        return Uni.combine().all().unis(clienteUni, appUni).asTuple()
            .map(tuple -> {
                ClienteObterResponse cliente = tuple.getItem1();
                AplicativoObterResponse app = tuple.getItem2();

                if (cliente != null && cliente.getCliente() != null) {
                    response.getLiberacao().setClienteNome(cliente.getCliente().getNome());
                }
                if (app != null && app.getAplicativo() != null) {
                    response.getLiberacao().setAplicativoDescricao(app.getAplicativo().getDescricao());
                }
                return response;
            });
    }
}

