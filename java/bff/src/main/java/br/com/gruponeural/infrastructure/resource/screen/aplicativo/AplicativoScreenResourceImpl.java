package br.com.gruponeural.infrastructure.resource.screen.aplicativo;

import org.eclipse.microprofile.openapi.annotations.parameters.Parameter;
import org.eclipse.microprofile.openapi.annotations.tags.Tag;

import br.com.gruponeural.application.resource.screen.aplicativo.AplicativoScreenResource;
import br.com.gruponeural.application.usecase.screen.aplicativo.AplicativoScreenAlterarUseCase;
import br.com.gruponeural.application.usecase.screen.aplicativo.AplicativoScreenCadastrarUseCase;
import br.com.gruponeural.application.usecase.screen.aplicativo.AplicativoScreenExcluirUseCase;
import br.com.gruponeural.application.usecase.screen.aplicativo.AplicativoScreenListarUseCase;
import br.com.gruponeural.application.usecase.screen.aplicativo.AplicativoScreenObterUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.aplicativo.AplicativoAlterarRequest;
import br.com.gruponeural.dto.aplicativo.AplicativoAlterarResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoCadastrarRequest;
import br.com.gruponeural.dto.aplicativo.AplicativoCadastrarResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoExcluirResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoListarResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoObterResponse;
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

@Path("v1/screen/aplicativo")
@Produces(MediaType.APPLICATION_JSON)
@Tag(name = "Aplicativo (tela)", description = "Operações da tela de aplicativo via Cortex")
@ApplicationScoped
public class AplicativoScreenResourceImpl implements AplicativoScreenResource {

    @Inject
    AplicativoScreenListarUseCase aplicativoScreenListarUseCase;

    @Inject
    AplicativoScreenCadastrarUseCase aplicativoScreenCadastrarUseCase;

    @Inject
    AplicativoScreenObterUseCase aplicativoScreenObterUseCase;

    @Inject
    AplicativoScreenAlterarUseCase aplicativoScreenAlterarUseCase;

    @Inject
    AplicativoScreenExcluirUseCase aplicativoScreenExcluirUseCase;

    @GET
    @Path("listar")
    @Override
    public Uni<AplicativoListarResponse> listar(
        @Parameter(description = "Número da página (1-based)", required = false)
        @QueryParam("pageNumber") Integer pageNumber,
        @Parameter(description = "Tamanho da página", required = false)
        @QueryParam("pageSize") Integer pageSize) {

        return aplicativoScreenListarUseCase
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
    public Uni<AplicativoCadastrarResponse> cadastrar(
        @Parameter(description = "Dados do novo aplicativo", required = true)
        AplicativoCadastrarRequest request) {

        return aplicativoScreenCadastrarUseCase
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
    public Uni<AplicativoObterResponse> obter(
        @Parameter(description = "Identificador do aplicativo", required = true)
        @PathParam("id") String id) {

        return aplicativoScreenObterUseCase
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
    public Uni<AplicativoAlterarResponse> alterar(
        @Parameter(description = "Identificador do aplicativo", required = true)
        @PathParam("id") String id,
        @Parameter(description = "Dados para alteração", required = true)
        AplicativoAlterarRequest request) {

        return aplicativoScreenAlterarUseCase
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
    public Uni<AplicativoExcluirResponse> excluir(
        @Parameter(description = "Identificador do aplicativo", required = true)
        @PathParam("id") String id) {

        return aplicativoScreenExcluirUseCase
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

