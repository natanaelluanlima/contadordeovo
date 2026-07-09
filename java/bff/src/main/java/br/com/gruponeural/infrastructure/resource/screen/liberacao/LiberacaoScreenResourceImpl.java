package br.com.gruponeural.infrastructure.resource.screen.liberacao;

import org.eclipse.microprofile.openapi.annotations.parameters.Parameter;
import org.eclipse.microprofile.openapi.annotations.tags.Tag;

import br.com.gruponeural.application.resource.screen.liberacao.LiberacaoScreenResource;
import br.com.gruponeural.application.usecase.screen.liberacao.LiberacaoScreenAlterarUseCase;
import br.com.gruponeural.application.usecase.screen.liberacao.LiberacaoScreenCadastrarUseCase;
import br.com.gruponeural.application.usecase.screen.liberacao.LiberacaoScreenExcluirUseCase;
import br.com.gruponeural.application.usecase.screen.liberacao.LiberacaoScreenListarUseCase;
import br.com.gruponeural.application.usecase.screen.liberacao.LiberacaoScreenObterUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.liberacao.LiberacaoAlterarRequest;
import br.com.gruponeural.dto.liberacao.LiberacaoAlterarResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoCadastrarRequest;
import br.com.gruponeural.dto.liberacao.LiberacaoCadastrarResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoExcluirResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoListarResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoObterResponse;
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

@Path("v1/screen/liberacao")
@Produces(MediaType.APPLICATION_JSON)
@Tag(name = "Liberação (tela)", description = "Operações da tela de liberação via Cortex")
@ApplicationScoped
public class LiberacaoScreenResourceImpl implements LiberacaoScreenResource {

    @Inject
    LiberacaoScreenListarUseCase liberacaoScreenListarUseCase;

    @Inject
    LiberacaoScreenCadastrarUseCase liberacaoScreenCadastrarUseCase;

    @Inject
    LiberacaoScreenObterUseCase liberacaoScreenObterUseCase;

    @Inject
    LiberacaoScreenAlterarUseCase liberacaoScreenAlterarUseCase;

    @Inject
    LiberacaoScreenExcluirUseCase liberacaoScreenExcluirUseCase;

    @GET
    @Path("listar")
    @Override
    public Uni<LiberacaoListarResponse> listar(
        @Parameter(description = "Número da página (1-based)", required = false)
        @QueryParam("pageNumber") Integer pageNumber,
        @Parameter(description = "Tamanho da página", required = false)
        @QueryParam("pageSize") Integer pageSize) {

        return liberacaoScreenListarUseCase
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
    public Uni<LiberacaoCadastrarResponse> cadastrar(
        @Parameter(description = "Dados da nova liberação", required = true)
        LiberacaoCadastrarRequest request) {

        return liberacaoScreenCadastrarUseCase
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
    public Uni<LiberacaoObterResponse> obter(
        @Parameter(description = "Identificador da liberação", required = true)
        @PathParam("id") String id) {

        return liberacaoScreenObterUseCase
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
    public Uni<LiberacaoAlterarResponse> alterar(
        @Parameter(description = "Identificador da liberação", required = true)
        @PathParam("id") String id,
        @Parameter(description = "Dados para alteração", required = true)
        LiberacaoAlterarRequest request) {

        return liberacaoScreenAlterarUseCase
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
    public Uni<LiberacaoExcluirResponse> excluir(
        @Parameter(description = "Identificador da liberação", required = true)
        @PathParam("id") String id) {

        return liberacaoScreenExcluirUseCase
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

