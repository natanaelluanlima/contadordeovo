package br.com.gruponeural.infrastructure.restclient.cortex.cortex;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import br.com.gruponeural.dto.liberacao.LiberacaoAlterarRequest;
import br.com.gruponeural.dto.liberacao.LiberacaoAlterarResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoCadastrarRequest;
import br.com.gruponeural.dto.liberacao.LiberacaoCadastrarResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoExcluirResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoListarResponse;
import br.com.gruponeural.dto.liberacao.LiberacaoObterResponse;
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
@Path("v1/liberacao")
@Produces(MediaType.APPLICATION_JSON)
public interface LiberacaoCortexRestClient {

    @GET
    @Path("listar")
    Uni<LiberacaoListarResponse> listar(
        @QueryParam("pageNumber") Integer pageNumber,
        @QueryParam("pageSize") Integer pageSize);

    @POST
    @Path("cadastrar")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<LiberacaoCadastrarResponse> cadastrar(LiberacaoCadastrarRequest body);

    @GET
    @Path("obter/{id}")
    Uni<LiberacaoObterResponse> obter(@PathParam("id") String id);

    @PUT
    @Path("alterar/{id}")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<LiberacaoAlterarResponse> alterar(@PathParam("id") String id, LiberacaoAlterarRequest body);

    @DELETE
    @Path("excluir/{id}")
    Uni<LiberacaoExcluirResponse> excluir(@PathParam("id") String id);
}

