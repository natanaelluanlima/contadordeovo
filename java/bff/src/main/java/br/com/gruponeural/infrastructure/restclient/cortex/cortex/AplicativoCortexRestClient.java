package br.com.gruponeural.infrastructure.restclient.cortex.cortex;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import br.com.gruponeural.dto.aplicativo.AplicativoAlterarRequest;
import br.com.gruponeural.dto.aplicativo.AplicativoAlterarResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoCadastrarRequest;
import br.com.gruponeural.dto.aplicativo.AplicativoCadastrarResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoExcluirResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoListarResponse;
import br.com.gruponeural.dto.aplicativo.AplicativoObterResponse;
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
@Path("v1/aplicativo")
@Produces(MediaType.APPLICATION_JSON)
public interface AplicativoCortexRestClient {

    @GET
    @Path("listar")
    Uni<AplicativoListarResponse> listar(
        @QueryParam("pageNumber") Integer pageNumber,
        @QueryParam("pageSize") Integer pageSize);

    @POST
    @Path("cadastrar")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<AplicativoCadastrarResponse> cadastrar(AplicativoCadastrarRequest body);

    @GET
    @Path("obter/{id}")
    Uni<AplicativoObterResponse> obter(@PathParam("id") String id);

    @PUT
    @Path("alterar/{id}")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<AplicativoAlterarResponse> alterar(@PathParam("id") String id, AplicativoAlterarRequest body);

    @DELETE
    @Path("excluir/{id}")
    Uni<AplicativoExcluirResponse> excluir(@PathParam("id") String id);
}

