package br.com.gruponeural.infrastructure.restclient.cortex.cortex;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import br.com.gruponeural.dto.usuario.UsuarioAlterarRequest;
import br.com.gruponeural.dto.usuario.UsuarioAlterarResponse;
import br.com.gruponeural.dto.usuario.UsuarioCadastrarRequest;
import br.com.gruponeural.dto.usuario.UsuarioCadastrarResponse;
import br.com.gruponeural.dto.usuario.UsuarioExcluirResponse;
import br.com.gruponeural.dto.usuario.UsuarioListarResponse;
import br.com.gruponeural.dto.usuario.UsuarioObterResponse;
import io.smallrye.mutiny.Uni;
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

@RegisterRestClient(configKey = "cortex-cortex")
@Path("v1/usuario")
@Produces(MediaType.APPLICATION_JSON)
public interface UsuarioCortexRestClient {

    @GET
    @Path("listar")
    Uni<UsuarioListarResponse> listar(
        @QueryParam("pageNumber") Integer pageNumber,
        @QueryParam("pageSize") Integer pageSize);

    @POST
    @Path("cadastrar")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<UsuarioCadastrarResponse> cadastrar(UsuarioCadastrarRequest body);

    @GET
    @Path("obter/{id}")
    Uni<UsuarioObterResponse> obter(@PathParam("id") String id);

    @PUT
    @Path("alterar/{id}")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<UsuarioAlterarResponse> alterar(@PathParam("id") String id, UsuarioAlterarRequest body);

    @DELETE
    @Path("excluir/{id}")
    Uni<UsuarioExcluirResponse> excluir(@PathParam("id") String id);
}
