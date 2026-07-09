package br.com.gruponeural.application.usecase.screen.liberacao.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import br.com.gruponeural.application.usecase.screen.liberacao.LiberacaoScreenListarUseCase;
import br.com.gruponeural.core.dto.response.PageResponse;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.aplicativo.AplicativoListarResponse;
import br.com.gruponeural.dto.cliente.ClienteListarResponse;
import br.com.gruponeural.dto.common.AplicativoDTO;
import br.com.gruponeural.dto.common.ClienteDTO;
import br.com.gruponeural.dto.common.LiberacaoDTO;
import br.com.gruponeural.dto.liberacao.LiberacaoListarResponse;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.AplicativoCortexRestClient;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.ClienteCortexRestClient;
import br.com.gruponeural.infrastructure.restclient.cortex.cortex.LiberacaoCortexRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class LiberacaoScreenListarUseCaseImpl implements LiberacaoScreenListarUseCase {

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
    public Uni<LiberacaoListarResponse> listar(Integer pageNumber, Integer pageSize) {
        return liberacaoCortexRestClient
            .listar(pageNumber, pageSize)
            .chain(this::enriquecer)
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setValuesName("liberacaoListarResponse")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setThrowable(throwable)
                .setText("Erro ao listar liberações no Cortex")
                .build());
    }

    private Uni<LiberacaoListarResponse> enriquecer(LiberacaoListarResponse liberacaoListarResponse) {
        if (liberacaoListarResponse == null || liberacaoListarResponse.getPagina() == null) {
            return Uni.createFrom().item(liberacaoListarResponse);
        }

        PageResponse<LiberacaoDTO> paginaLiberacao = liberacaoListarResponse.getPagina();
        List<LiberacaoDTO> items = paginaLiberacao.getItems();
        if (items == null || items.isEmpty()) {
            return Uni.createFrom().item(liberacaoListarResponse);
        }

        Uni<Map<UUID, String>> clientesUni = listarTodosClientes()
            .map(this::mapearClientesPorId);
        Uni<Map<UUID, String>> appsUni = listarTodosAplicativos()
            .map(this::mapearAplicativosPorId);

        return Uni.combine().all().unis(clientesUni, appsUni).asTuple()
            .map(tuple -> {
                Map<UUID, String> clienteNomePorId = tuple.getItem1();
                Map<UUID, String> appDescPorId = tuple.getItem2();

                for (LiberacaoDTO l : items) {
                    if (l == null) {
                        continue;
                    }
                    if (l.getIdCliente() != null) {
                        l.setClienteNome(clienteNomePorId.get(l.getIdCliente()));
                    }
                    if (l.getIdAplicativo() != null) {
                        l.setAplicativoDescricao(appDescPorId.get(l.getIdAplicativo()));
                    }
                }
                return liberacaoListarResponse;
            });
    }

    private Map<UUID, String> mapearClientesPorId(List<ClienteDTO> clientes) {
        Map<UUID, String> map = new HashMap<>();
        if (clientes == null) {
            return map;
        }
        for (ClienteDTO c : clientes) {
            if (c != null && c.getId() != null) {
                map.put(c.getId(), c.getNome());
            }
        }
        return map;
    }

    private Map<UUID, String> mapearAplicativosPorId(List<AplicativoDTO> apps) {
        Map<UUID, String> map = new HashMap<>();
        if (apps == null) {
            return map;
        }
        for (AplicativoDTO a : apps) {
            if (a != null && a.getId() != null) {
                map.put(a.getId(), a.getDescricao());
            }
        }
        return map;
    }

    private Uni<List<ClienteDTO>> listarTodosClientes() {
        return clienteCortexRestClient
            .listar(1, 100)
            .chain(first -> {
                List<ClienteDTO> all = new ArrayList<>();
                PageResponse<ClienteDTO> page = first == null ? null : first.getPagina();
                if (page == null || page.getItems() == null) {
                    return Uni.createFrom().item(all);
                }
                all.addAll(page.getItems());
                int totalPages = page.getTotalPages() == null ? 1 : page.getTotalPages();
                if (totalPages <= 1) {
                    return Uni.createFrom().item(all);
                }

                List<Uni<ClienteListarResponse>> calls = new ArrayList<>();
                for (int p = 2; p <= totalPages; p++) {
                    calls.add(clienteCortexRestClient.listar(p, 100));
                }
                return Uni.combine().all().unis(calls).with(list -> {
                    for (Object o : list) {
                        ClienteListarResponse r = (ClienteListarResponse) o;
                        if (r != null && r.getPagina() != null && r.getPagina().getItems() != null) {
                            all.addAll(r.getPagina().getItems());
                        }
                    }
                    return all;
                });
            });
    }

    private Uni<List<AplicativoDTO>> listarTodosAplicativos() {
        return aplicativoCortexRestClient
            .listar(1, 100)
            .chain(first -> {
                List<AplicativoDTO> all = new ArrayList<>();
                PageResponse<AplicativoDTO> page = first == null ? null : first.getPagina();
                if (page == null || page.getItems() == null) {
                    return Uni.createFrom().item(all);
                }
                all.addAll(page.getItems());
                int totalPages = page.getTotalPages() == null ? 1 : page.getTotalPages();
                if (totalPages <= 1) {
                    return Uni.createFrom().item(all);
                }

                List<Uni<AplicativoListarResponse>> calls = new ArrayList<>();
                for (int p = 2; p <= totalPages; p++) {
                    calls.add(aplicativoCortexRestClient.listar(p, 100));
                }
                return Uni.combine().all().unis(calls).with(list -> {
                    for (Object o : list) {
                        AplicativoListarResponse r = (AplicativoListarResponse) o;
                        if (r != null && r.getPagina() != null && r.getPagina().getItems() != null) {
                            all.addAll(r.getPagina().getItems());
                        }
                    }
                    return all;
                });
            });
    }
}

