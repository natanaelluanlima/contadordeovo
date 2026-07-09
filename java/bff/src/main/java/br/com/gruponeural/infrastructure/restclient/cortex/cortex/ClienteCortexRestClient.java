package br.com.gruponeural.infrastructure.restclient.cortex.cortex;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import br.com.gruponeural.dto.cliente.ClienteAlterarRequest;
import br.com.gruponeural.dto.cliente.ClienteAlterarResponse;
import br.com.gruponeural.dto.cliente.ClienteCadastrarRequest;
import br.com.gruponeural.dto.cliente.ClienteCadastrarResponse;
import br.com.gruponeural.dto.cliente.ClienteExcluirResponse;
import br.com.gruponeural.dto.cliente.ClienteListarResponse;
import br.com.gruponeural.dto.cliente.ClienteObterResponse;
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
@Path("v1/cliente")
@Produces(MediaType.APPLICATION_JSON)
public interface ClienteCortexRestClient {

    @GET
    @Path("listar")
    Uni<ClienteListarResponse> listar(
        @QueryParam("pageNumber") Integer pageNumber,
        @QueryParam("pageSize") Integer pageSize);

    @POST
    @Path("cadastrar")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<ClienteCadastrarResponse> cadastrar(ClienteCadastrarRequest body);

    @GET
    @Path("obter/{id}")
    Uni<ClienteObterResponse> obter(@PathParam("id") String id);

    @PUT
    @Path("alterar/{id}")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<ClienteAlterarResponse> alterar(@PathParam("id") String id, ClienteAlterarRequest body);

    @DELETE
    @Path("excluir/{id}")
    Uni<ClienteExcluirResponse> excluir(@PathParam("id") String id);
}

