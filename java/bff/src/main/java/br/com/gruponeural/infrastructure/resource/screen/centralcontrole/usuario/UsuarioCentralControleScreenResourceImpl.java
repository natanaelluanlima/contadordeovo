package br.com.gruponeural.infrastructure.resource.screen.centralcontrole.usuario;

import org.eclipse.microprofile.openapi.annotations.parameters.Parameter;
import org.eclipse.microprofile.openapi.annotations.tags.Tag;

import br.com.gruponeural.application.resource.screen.centralcontrole.usuario.UsuarioCentralControleScreenResource;
import br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.UsuarioCentralControleScreenAlterarUseCase;
import br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.UsuarioCentralControleScreenCadastrarUseCase;
import br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.UsuarioCentralControleScreenExcluirUseCase;
import br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.UsuarioCentralControleScreenListarUseCase;
import br.com.gruponeural.application.usecase.screen.centralcontrole.usuario.UsuarioCentralControleScreenObterUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.usuario.UsuarioAlterarRequest;
import br.com.gruponeural.dto.usuario.UsuarioAlterarResponse;
import br.com.gruponeural.dto.usuario.UsuarioCadastrarRequest;
import br.com.gruponeural.dto.usuario.UsuarioCadastrarResponse;
import br.com.gruponeural.dto.usuario.UsuarioExcluirResponse;
import br.com.gruponeural.dto.usuario.UsuarioListarResponse;
import br.com.gruponeural.dto.usuario.UsuarioObterResponse;
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

@Path("v1/screen/centralcontrole/usuario")
@Produces(MediaType.APPLICATION_JSON)
@Tag(
    name = "Usuario Central de Controle (tela)",
    description = "CRUD via MS Central de Controle (OpenAPI: http://localhost:3002/documentacao/).")
@ApplicationScoped
public class UsuarioCentralControleScreenResourceImpl implements UsuarioCentralControleScreenResource {

    @Inject
    UsuarioCentralControleScreenListarUseCase usuarioCentralControleScreenListarUseCase;

    @Inject
    UsuarioCentralControleScreenCadastrarUseCase usuarioCentralControleScreenCadastrarUseCase;

    @Inject
    UsuarioCentralControleScreenObterUseCase usuarioCentralControleScreenObterUseCase;

    @Inject
    UsuarioCentralControleScreenAlterarUseCase usuarioCentralControleScreenAlterarUseCase;

    @Inject
    UsuarioCentralControleScreenExcluirUseCase usuarioCentralControleScreenExcluirUseCase;

    @GET
    @Path("listar")
    @Override
    public Uni<UsuarioListarResponse> listar(
        @Parameter(description = "Número da página (1-based)", required = false)
        @QueryParam("pageNumber") Integer pageNumber,
        @Parameter(description = "Tamanho da página", required = false)
        @QueryParam("pageSize") Integer pageSize) {

        return usuarioCentralControleScreenListarUseCase
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
    public Uni<UsuarioCadastrarResponse> cadastrar(
        @Parameter(description = "Dados do novo usuário", required = true)
        UsuarioCadastrarRequest request) {

        return usuarioCentralControleScreenCadastrarUseCase
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
    public Uni<UsuarioObterResponse> obter(
        @Parameter(description = "Identificador do usuário", required = true)
        @PathParam("id") String id) {

        return usuarioCentralControleScreenObterUseCase
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
    public Uni<UsuarioAlterarResponse> alterar(
        @Parameter(description = "Identificador do usuário", required = true)
        @PathParam("id") String id,
        @Parameter(description = "Dados para alteração", required = true)
        UsuarioAlterarRequest request) {

        return usuarioCentralControleScreenAlterarUseCase
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
    public Uni<UsuarioExcluirResponse> excluir(
        @Parameter(description = "Identificador do usuário", required = true)
        @PathParam("id") String id) {

        return usuarioCentralControleScreenExcluirUseCase
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
