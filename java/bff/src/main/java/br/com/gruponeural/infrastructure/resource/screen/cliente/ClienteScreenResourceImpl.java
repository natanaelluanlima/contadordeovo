package br.com.gruponeural.infrastructure.resource.screen.cliente;

import org.eclipse.microprofile.openapi.annotations.parameters.Parameter;
import org.eclipse.microprofile.openapi.annotations.tags.Tag;

import br.com.gruponeural.application.resource.screen.cliente.ClienteScreenResource;
import br.com.gruponeural.application.usecase.screen.cliente.ClienteScreenAlterarUseCase;
import br.com.gruponeural.application.usecase.screen.cliente.ClienteScreenCadastrarUseCase;
import br.com.gruponeural.application.usecase.screen.cliente.ClienteScreenExcluirUseCase;
import br.com.gruponeural.application.usecase.screen.cliente.ClienteScreenListarUseCase;
import br.com.gruponeural.application.usecase.screen.cliente.ClienteScreenObterUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.cliente.ClienteAlterarRequest;
import br.com.gruponeural.dto.cliente.ClienteAlterarResponse;
import br.com.gruponeural.dto.cliente.ClienteCadastrarRequest;
import br.com.gruponeural.dto.cliente.ClienteCadastrarResponse;
import br.com.gruponeural.dto.cliente.ClienteExcluirResponse;
import br.com.gruponeural.dto.cliente.ClienteListarResponse;
import br.com.gruponeural.dto.cliente.ClienteObterResponse;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.PUT;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

@Path("v1/screen/cliente")
@Produces(MediaType.APPLICATION_JSON)
@Tag(name = "Cliente (tela)", description = "Operações da tela de cliente via Cortex")
@ApplicationScoped
public class ClienteScreenResourceImpl implements ClienteScreenResource {

    @Inject
    ClienteScreenListarUseCase clienteScreenListarUseCase;

    @Inject
    ClienteScreenCadastrarUseCase clienteScreenCadastrarUseCase;

    @Inject
    ClienteScreenObterUseCase clienteScreenObterUseCase;

    @Inject
    ClienteScreenAlterarUseCase clienteScreenAlterarUseCase;

    @Inject
    ClienteScreenExcluirUseCase clienteScreenExcluirUseCase;

    @GET
    @Path("listar")
    @Override
    public Uni<ClienteListarResponse> listar(
        @Parameter(description = "Número da página (1-based)", required = false)
        @QueryParam("pageNumber") Integer pageNumber,
        @Parameter(description = "Tamanho da página", required = false)
        @QueryParam("pageSize") Integer pageSize) {

        return clienteScreenListarUseCase
            .listar(pageNumber, pageSize)
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("listar")
                .setThrowable(throwable)
                .build());
    }

    @POST
    @Path("cadastrar")
    @Consumes(MediaType.APPLICATION_JSON)
    @Override
    public Uni<ClienteCadastrarResponse> cadastrar(
        @Parameter(description = "Dados do novo cliente", required = true)
        ClienteCadastrarRequest request) {

        return clienteScreenCadastrarUseCase
            .cadastrar(request)
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("cadastrar")
                .setThrowable(throwable)
                .build());
    }

    @GET
    @Path("obter/{id}")
    @Override
    public Uni<ClienteObterResponse> obter(
        @Parameter(description = "Identificador do cliente", required = true)
        @PathParam("id") String id) {

        return clienteScreenObterUseCase
            .obter(id)
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("obter")
                .setThrowable(throwable)
                .build());
    }

    @PUT
    @Path("alterar/{id}")
    @Consumes(MediaType.APPLICATION_JSON)
    @Override
    public Uni<ClienteAlterarResponse> alterar(
        @Parameter(description = "Identificador do cliente", required = true)
        @PathParam("id") String id,
        @Parameter(description = "Dados para alteração", required = true)
        ClienteAlterarRequest request) {

        return clienteScreenAlterarUseCase
            .alterar(id, request)
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("alterar")
                .setThrowable(throwable)
                .build());
    }

    @DELETE
    @Path("excluir/{id}")
    @Override
    public Uni<ClienteExcluirResponse> excluir(
        @Parameter(description = "Identificador do cliente", required = true)
        @PathParam("id") String id) {

        return clienteScreenExcluirUseCase
            .excluir(id)
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("excluir")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("excluir")
                .setThrowable(throwable)
                .build());
    }
}

