package br.com.gruponeural.infrastructure.resource.screen.usuario;

import org.eclipse.microprofile.openapi.annotations.parameters.Parameter;
import org.eclipse.microprofile.openapi.annotations.tags.Tag;

import br.com.gruponeural.application.resource.screen.usuario.UsuarioScreenResource;
import br.com.gruponeural.application.usecase.screen.usuario.UsuarioScreenAlterarUseCase;
import br.com.gruponeural.application.usecase.screen.usuario.UsuarioScreenCadastrarUseCase;
import br.com.gruponeural.application.usecase.screen.usuario.UsuarioScreenExcluirUseCase;
import br.com.gruponeural.application.usecase.screen.usuario.UsuarioScreenListarUseCase;
import br.com.gruponeural.application.usecase.screen.usuario.UsuarioScreenObterUseCase;
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

@Path("v1/screen/usuario")
@Produces(MediaType.APPLICATION_JSON)
@Tag(name = "Usuario (tela)", description = "Operações da tela de usuário via Cortex")
@ApplicationScoped
public class UsuarioScreenResourceImpl implements UsuarioScreenResource {

    @Inject
    UsuarioScreenListarUseCase usuarioScreenListarUseCase;

    @Inject
    UsuarioScreenCadastrarUseCase usuarioScreenCadastrarUseCase;

    @Inject
    UsuarioScreenObterUseCase usuarioScreenObterUseCase;

    @Inject
    UsuarioScreenAlterarUseCase usuarioScreenAlterarUseCase;

    @Inject
    UsuarioScreenExcluirUseCase usuarioScreenExcluirUseCase;

    @GET
    @Path("listar")
    @Override
    public Uni<UsuarioListarResponse> listar(
        @Parameter(description = "Número da página (1-based)", required = false)
        @QueryParam("pageNumber") Integer pageNumber,
        @Parameter(description = "Tamanho da página", required = false)
        @QueryParam("pageSize") Integer pageSize) {

        return usuarioScreenListarUseCase
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

        return usuarioScreenCadastrarUseCase
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

        return usuarioScreenObterUseCase
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

        return usuarioScreenAlterarUseCase
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

        return usuarioScreenExcluirUseCase
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
