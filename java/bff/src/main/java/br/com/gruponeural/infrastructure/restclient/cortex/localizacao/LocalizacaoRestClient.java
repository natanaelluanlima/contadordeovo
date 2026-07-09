package br.com.gruponeural.infrastructure.restclient.cortex.localizacao;

import java.util.List;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import br.com.gruponeural.dto.localizacao.BairroAlterarRequest;
import br.com.gruponeural.dto.localizacao.BairroCadastrarRequest;
import br.com.gruponeural.dto.localizacao.BairroExcluirResponse;
import br.com.gruponeural.dto.localizacao.BairroObterResponse;
import br.com.gruponeural.dto.localizacao.LocalizacaoItemDTO;
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

@RegisterRestClient(configKey = "cortex-localizacao")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public interface LocalizacaoRestClient {

    @GET
    @Path("v1/estado/listar")
    Uni<List<LocalizacaoItemDTO>> listarEstados();

    @GET
    @Path("v1/cidade/listar")
    Uni<List<LocalizacaoItemDTO>> listarCidades(@QueryParam("idEstado") String idEstado);

    @GET
    @Path("v1/bairro/listar")
    Uni<List<LocalizacaoItemDTO>> listarBairros(@QueryParam("idCidade") String idCidade);

    @POST
    @Path("v1/bairro/criar")
    Uni<LocalizacaoItemDTO> cadastrarBairro(
        @QueryParam("idCidade") String idCidade,
        BairroCadastrarRequest body);

    @GET
    @Path("v1/bairro/obter/{id}")
    Uni<BairroObterResponse> obterBairro(@PathParam("id") String id);

    @PUT
    @Path("v1/bairro/alterar/{id}")
    Uni<LocalizacaoItemDTO> alterarBairro(@PathParam("id") String id, BairroAlterarRequest body);

    @DELETE
    @Path("v1/bairro/excluir/{id}")
    Uni<BairroExcluirResponse> excluirBairro(@PathParam("id") String id);
}
